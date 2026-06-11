// DO NOT TOUCH ORDER
import './global'

// Collapsible animates through the `anim` global. It used to be loaded
// indirectly (combobox -> select -> dropdown -> anime) before the combobox
// moved to Vuetify; load it explicitly.
import 'materialize-css/js/anime.min';
import 'materialize-css/js/collapsible';
import 'materialize-css/sass/components/_collapsible.scss';