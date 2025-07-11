/**
 * Parameter History Utility
 * Manages saving and loading of parameter values to/from localStorage
 */

const PARAMETER_HISTORY_PREFIX = 'script_server_param_history_';
const MAX_HISTORY_ENTRIES = 10;

/**
 * Get the storage key for a specific script's parameter history
 * @param {string} scriptName - The name of the script
 * @returns {string} The storage key
 */
function getStorageKey(scriptName) {
    return PARAMETER_HISTORY_PREFIX + scriptName;
}

/**
 * Save parameter values to localStorage for a specific script
 * @param {string} scriptName - The name of the script
 * @param {Object} parameterValues - The parameter values to save
 */
export function saveParameterHistory(scriptName, parameterValues) {
    try {
        const key = getStorageKey(scriptName);
        const history = loadParameterHistory(scriptName);

        // check if parameterValues is empty
        if (Object.keys(parameterValues).length === 0) {
            return;
        }
        
        // Add current values to history (avoid duplicates)
        const newEntry = {
            timestamp: Date.now(),
            values: { ...parameterValues }
        };
        
        // Remove any existing entry with the same values
        const filteredHistory = history.filter(entry => 
            JSON.stringify(entry.values) !== JSON.stringify(newEntry.values)
        );
        
        // Add new entry at the beginning
        filteredHistory.unshift(newEntry);
        
        // Keep only the most recent entries
        if (filteredHistory.length > MAX_HISTORY_ENTRIES) {
            filteredHistory.splice(MAX_HISTORY_ENTRIES);
        }
        
        localStorage.setItem(key, JSON.stringify(filteredHistory));
    } catch (error) {
        console.warn('Failed to save parameter history:', error);
    }
}

/**
 * Load parameter history from localStorage for a specific script
 * @param {string} scriptName - The name of the script
 * @returns {Array} Array of historical parameter entries
 */
export function loadParameterHistory(scriptName) {
    try {
        const key = getStorageKey(scriptName);
        const stored = localStorage.getItem(key);
        return stored ? JSON.parse(stored) : [];
    } catch (error) {
        console.warn('Failed to load parameter history:', error);
        return [];
    }
}

/**
 * Get the most recent parameter values for a script
 * @param {string} scriptName - The name of the script
 * @returns {Object|null} The most recent parameter values or null if no history
 */
export function getMostRecentValues(scriptName) {
    const history = loadParameterHistory(scriptName);
    return history.length > 0 ? history[0].values : null;
}

/**
 * Remove a specific parameter history entry for a script
 * @param {string} scriptName - The name of the script
 * @param {number} index - The index of the entry to remove (0-based)
 */
export function removeParameterHistoryEntry(scriptName, index) {
    try {
        const key = getStorageKey(scriptName);
        const history = loadParameterHistory(scriptName);
        
        // Check if the index is valid
        if (index < 0 || index >= history.length) {
            console.warn(`Invalid index: ${index} for script: ${scriptName}`);
            return;
        }
        
        // Remove the entry at the specified index
        history.splice(index, 1);
        
        // Save the updated history back to localStorage
        localStorage.setItem(key, JSON.stringify(history));
    } catch (error) {
        console.warn('Failed to remove parameter history entry:', error);
    }
}