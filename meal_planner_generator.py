<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Structured AI Meal Planner</title>
    <!-- Load Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Custom font and basic styling */
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f7f7f7;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container-card {
            max-width: 900px;
            width: 95%;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }
        .loading-indicator {
            border-top-color: #0b72e5;
            -webkit-animation: spinner 0.8s linear infinite;
            animation: spinner 0.8s linear infinite;
        }
        @-webkit-keyframes spinner {
            0% { -webkit-transform: rotate(0deg); }
            100% { -webkit-transform: rotate(360deg); }
        }
        @keyframes spinner {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body class="p-4">

<div class="container-card bg-white p-6 md:p-10 rounded-xl">
    <h1 class="text-3xl md:text-4xl font-extrabold text-gray-900 mb-2">Structured Meal Planner AI</h1>
    <p class="text-md text-gray-500 mb-8">This app demonstrates **JSON Schema enforcement** by guaranteeing a predictable, structured meal plan output from the Gemini API.</p>

    <!-- User Input Form -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div>
            <label for="cuisine" class="block text-sm font-medium text-gray-700 mb-1">Cuisine Style</label>
            <input type="text" id="cuisine" value="Mediterranean" placeholder="e.g., Italian, Vegan, Low-Carb" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500">
        </div>
        <div>
            <label for="allergens" class="block text-sm font-medium text-gray-700 mb-1">Allergens / Dietary Needs (Optional)</label>
            <input type="text" id="allergens" value="Gluten-free, no peanuts" placeholder="e.g., Dairy-free, no pork" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500">
        </div>
    </div>
    
    <button id="generateButton" 
            onclick="generateMealPlan()"
            class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition duration-200 shadow-md flex items-center justify-center">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5 mr-2">
            <path fill-rule="evenodd" d="M11.47 2.47a.75.75 0 0 1 1.06 0l7.5 7.5a.75.75 0 1 1-1.06 1.06L12 4.06 4.03 11.03a.75.75 0 0 1-1.06-1.06l7.5-7.5Z" clip-rule="evenodd" />
            <path fill-rule="evenodd" d="M12 2.25a.75.75 0 0 1 .75.75v16.19l1.72-1.72a.75.75 0 1 1 1.06 1.06l-3 3a.75.75 0 0 1-1.06 0l-3-3a.75.75 0 1 1 1.06-1.06l1.72 1.72V3a.75.75 0 0 1 .75-.75Z" clip-rule="evenodd" />
        </svg>
        Generate Meal Plan
    </button>
    
    <!-- Output Section -->
    <div class="mt-8">
        <h2 class="text-xl font-bold text-gray-800 mb-4 border-b pb-2">Generated Meal Plan (JSON Output)</h2>
        
        <div id="loading" class="hidden flex items-center justify-center p-8">
            <div class="loading-indicator ease-linear rounded-full border-4 border-t-4 border-gray-200 h-12 w-12 mr-4"></div>
            <span class="text-blue-600 font-medium">Generating structured plan...</span>
        </div>

        <div id="error-message" class="hidden p-4 bg-red-100 text-red-700 border border-red-400 rounded-lg"></div>

        <pre id="jsonOutput" class="bg-gray-800 text-green-300 p-4 rounded-lg text-sm overflow-x-auto whitespace-pre-wrap"></pre>

        <div id="parsedOutput" class="mt-6">
            <!-- Parsed and rendered table goes here -->
        </div>
    </div>
</div>

<script>
    // Set mandatory API key and model URL
    const apiKey = ""; 
    // FIX APPLIED HERE: Changed to the mandatory current model name
    const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${apiKey}`;

    // --- JSON Schema Definition (The Proof Point for Your Resume) ---
    // This schema strictly defines the structure of the model's output.
    const MEAL_PLAN_SCHEMA = {
        type: "ARRAY",
        description: "A comprehensive meal plan array for one week.",
        items: {
            type: "OBJECT",
            properties: {
                day: { type: "STRING", description: "The day of the week (e.g., Monday)." },
                meals: {
                    type: "ARRAY",
                    items: {
                        type: "OBJECT",
                        properties: {
                            mealType: { type: "STRING", description: "Breakfast, Lunch, or Dinner." },
                            recipeName: { type: "STRING", description: "The name of the recipe." },
                            description: { type: "STRING", description: "A brief description of the meal." },
                            calories: { type: "INTEGER", description: "Estimated caloric count." }
                        },
                        propertyOrdering: ["mealType", "recipeName", "description", "calories"]
                    },
                    description: "List of meals for the specific day."
                }
            },
            propertyOrdering: ["day", "meals"]
        }
    };

    /**
     * Helper function for exponential backoff during API calls.
     * @param {number} attempt The current retry attempt number.
     * @returns {number} The delay in milliseconds.
     */
    function getDelay(attempt) {
        return Math.pow(2, attempt) * 1000 + Math.random() * 1000;
    }

    /**
     * Main function to call the Gemini API with structured output enforcement.
     */
    async function generateMealPlan() {
        const cuisine = document.getElementById('cuisine').value;
        const allergens = document.getElementById('allergens').value;
        const jsonOutput = document.getElementById('jsonOutput');
        const parsedOutput = document.getElementById('parsedOutput');
        const loading = document.getElementById('loading');
        const errorDiv = document.getElementById('error-message');
        const button = document.getElementById('generateButton');

        // Reset UI
        jsonOutput.textContent = '';
        parsedOutput.innerHTML = '';
        errorDiv.textContent = '';
        errorDiv.classList.add('hidden');
        button.disabled = true;
        loading.classList.remove('hidden');

        const prompt = `Create a 7-day meal plan. The cuisine style should be '${cuisine}'.
                        The plan must account for the following dietary needs/allergens: '${allergens}'.
                        The final output MUST strictly adhere to the provided JSON Schema for structured data enforcement.`;

        const payload = {
            contents: [{ parts: [{ text: prompt }] }],
            generationConfig: {
                responseMimeType: "application/json",
                responseSchema: MEAL_PLAN_SCHEMA
            },
            // The model is set via the apiUrl constant above (the fix is here)
        };

        const maxRetries = 3;
        let response = null;

        for (let attempt = 0; attempt < maxRetries; attempt++) {
            try {
                response = await fetch(apiUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    break; // Success! Exit loop.
                }

                // If response is not ok (e.g., 429, 500, etc.), retry (excluding 403/404 which won't fix themselves)
                if (response.status === 403 || response.status === 404) {
                    throw new Error(`API Error ${response.status}: ${response.statusText}. Check model name or API key permissions.`);
                }

                if (attempt < maxRetries - 1) {
                    const delay = getDelay(attempt);
                    // console.log(`Attempt ${attempt + 1} failed. Retrying in ${delay / 1000}s...`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                } else {
                    throw new Error(`Failed after ${maxRetries} attempts: ${response.statusText}`);
                }

            } catch (error) {
                loading.classList.add('hidden');
                errorDiv.textContent = `Error: ${error.message}. Please check your browser console for details.`;
                errorDiv.classList.remove('hidden');
                button.disabled = false;
                return;
            }
        }

        loading.classList.add('hidden');
        button.disabled = false;

        try {
            const result = await response.json();
            const jsonText = result.candidates?.[0]?.content?.parts?.[0]?.text;

            if (!jsonText) {
                const errorMessage = result.error?.message || 'Model generated no content or an unexpected error occurred.';
                jsonOutput.textContent = `API Response Error:\n${JSON.stringify(result, null, 2)}`;
                errorDiv.textContent = `Generation Failed: ${errorMessage}`;
                errorDiv.classList.remove('hidden');
                return;
            }

            // Display raw JSON output
            jsonOutput.textContent = jsonText;

            // Parse and render the structured output
            const parsedData = JSON.parse(jsonText);
            renderMealPlanTable(parsedData, parsedOutput);

        } catch (e) {
            errorDiv.textContent = `Parsing Error: The model did not return valid JSON. ${e.message}`;
            errorDiv.classList.remove('hidden');
            // Show any response we received if parsing failed
            if (response) {
                 jsonOutput.textContent = await response.text();
            }
        }
    }

    /**
     * Renders the structured meal plan data into a readable HTML table.
     * @param {Array<Object>} data The parsed meal plan array.
     * @param {HTMLElement} container The container to render the table into.
     */
    function renderMealPlanTable(data, container) {
        let html = '<div class="space-y-6">';

        data.forEach(dayPlan => {
            html += `
                <div class="border border-gray-200 rounded-xl overflow-hidden">
                    <h3 class="bg-blue-100 text-blue-800 text-lg font-semibold p-4">${dayPlan.day}</h3>
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/5">Meal</th>
                                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-2/5">Recipe</th>
                                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-2/5">Description</th>
                                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/5">Calories</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
            `;
            
            dayPlan.meals.forEach(meal => {
                html += `
                    <tr class="hover:bg-gray-50">
                        <td class="px-4 py-2 whitespace-nowrap text-sm font-medium text-gray-900">${meal.mealType}</td>
                        <td class="px-4 py-2 text-sm text-gray-800">${meal.recipeName}</td>
                        <td class="px-4 py-2 text-sm text-gray-500">${meal.description}</td>
                        <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-500">${meal.calories}</td>
                    </tr>
                `;
            });

            html += `
                        </tbody>
                    </table>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
    }
</script>

</body>
</html>
