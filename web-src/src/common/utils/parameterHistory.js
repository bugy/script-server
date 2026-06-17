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
            values: { ...parameterValues },
            favorite: false
        };
        
        // Check if an entry with the same values already exists
        const existingEntryIndex = history.findIndex(entry => 
            JSON.stringify(entry.values) === JSON.stringify(newEntry.values)
        );
        
        let filteredHistory;
        if (existingEntryIndex !== -1) {
            // If entry exists, preserve its favorite status and update timestamp
            filteredHistory = [...history];
            filteredHistory[existingEntryIndex] = {
                ...filteredHistory[existingEntryIndex],
                timestamp: Date.now()
            };
        } else {
            // If no duplicate exists, add new entry at the beginning
            filteredHistory = [newEntry, ...history];
        }
        
        // Keep only the most recent entries (excluding favorites)
        const nonFavoriteEntries = filteredHistory.filter(entry => !entry.favorite);
        const favoriteEntries = filteredHistory.filter(entry => entry.favorite);
        
        // Limit non-favorite entries
        if (nonFavoriteEntries.length > MAX_HISTORY_ENTRIES) {
            nonFavoriteEntries.splice(MAX_HISTORY_ENTRIES);
        }
        
        // Combine favorites first, then non-favorites
        const finalHistory = [...favoriteEntries, ...nonFavoriteEntries];
        
        localStorage.setItem(key, JSON.stringify(finalHistory));
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
        const history = stored ? JSON.parse(stored) : [];
        
        // Ensure all entries have the favorite property (for backward compatibility)
        return history.map(entry => ({
            ...entry,
            favorite: entry.favorite || false
        }));
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
        
        // Don't allow removal of favorite entries
        if (history[index].favorite) {
            console.warn('Cannot remove favorite entry');
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

/**
 * Toggle favorite status of a parameter history entry
 * @param {string} scriptName - The name of the script
 * @param {number} index - The index of the entry to toggle (0-based)
 */
export function toggleFavoriteEntry(scriptName, index) {
    try {
        const key = getStorageKey(scriptName);
        const history = loadParameterHistory(scriptName);
        
        // Check if the index is valid
        if (index < 0 || index >= history.length) {
            console.warn(`Invalid index: ${index} for script: ${scriptName}`);
            return;
        }
        
        // Toggle favorite status
        history[index].favorite = !history[index].favorite;
        
        // Reorder entries: favorites first, then non-favorites
        const favoriteEntries = history.filter(entry => entry.favorite);
        const nonFavoriteEntries = history.filter(entry => !entry.favorite);

        // Limit non-favorite entries
        if (nonFavoriteEntries.length > MAX_HISTORY_ENTRIES) {
            nonFavoriteEntries.splice(MAX_HISTORY_ENTRIES);
        }
        
        // Combine favorites first, then non-favorites
        const finalHistory = [...favoriteEntries, ...nonFavoriteEntries];
        
        // Save the updated history back to localStorage
        localStorage.setItem(key, JSON.stringify(finalHistory));
    } catch (error) {
        console.warn('Failed to toggle favorite entry:', error);
    }
}

/**
 * Check if historical values should be used for a script
 * @param {string} scriptName - The name of the script
 * @returns {boolean} True if historical values should be used, false otherwise
 */
export function shouldUseHistoricalValues(scriptName) {
    try {
        return localStorage.getItem(`useHistoricalValues_${scriptName}`) === 'true';
    } catch (error) {
        console.warn('Failed to check historical values toggle:', error);
        return false;
    }
}