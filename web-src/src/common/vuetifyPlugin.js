/**
 * Shared Vuetify 4 instance for all three apps (main, admin, login).
 *
 * The theme mirrors the palette of src/assets/css/shared.css (:root CSS variables).
 */
import {createVuetify} from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import {aliases, md} from 'vuetify/iconsets/md'
import 'vuetify/styles'

export default createVuetify({
    components,
    directives,
    icons: {
        // Reuses the Material Icons font (material-design-icons package) already
        // shipped by the app, avoiding a separate MDI font dependency.
        defaultSet: 'md',
        aliases,
        sets: {md}
    },
    theme: {
        defaultTheme: 'scriptServer',
        themes: {
            scriptServer: {
                dark: false,
                colors: {
                    // --primary-color / --primary-color-dark-color
                    primary: '#26a69a',
                    'primary-darken-1': '#00796B',
                    secondary: '#26a69a',
                    error: '#F44336',
                    // --background-color / --surface-color
                    background: '#FFFFFF',
                    surface: '#FFFFFF'
                }
            }
        }
    },
    defaults: {
        // Denser than MD3 defaults to match the app's compact visual style
        VCheckbox: {density: 'compact', hideDetails: true, color: 'primary'}
    }
})
