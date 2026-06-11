/**
 * Shared Vuetify 4 instance for all three apps (main, admin, login).
 *
 * Migration note (materialize -> Vuetify): during the transition both UI
 * libraries coexist. Vuetify 4 ships its styles inside CSS layers, which have
 * a *lower* priority than materialize's classic (unlayered) global styles —
 * so Vuetify components keep their look as long as materialize doesn't target
 * the same elements with bare element selectors. Conflicts must be resolved
 * per migrated component.
 *
 * The theme mirrors the palette of src/assets/css/shared.css (:root CSS
 * variables). The optional runtime conf/theme/theme.css override will be
 * bridged to Vuetify theme variables in the layout phase of the migration.
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
        // The app already ships Google's Material Icons font
        // (material-design-icons package, used as <i class="material-icons">),
        // so reuse it for Vuetify instead of adding the MDI font dependency.
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
        // materialize visuals are dense compared to MD3 defaults
        VCheckbox: {density: 'compact', hideDetails: true, color: 'primary'}
    }
})
