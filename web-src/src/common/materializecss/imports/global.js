import 'materialize-css/js/cash';
import 'materialize-css/js/global';
import 'materialize-css/js/waves';
// component.js has no exports; the Vite plugin `materialize-component-export`
// appends `export default Component;` at build time so we can import it here
// and expose it as a global for the IIFE-based materialize component files.
import Component from 'materialize-css/js/component.js';

globalThis.Component = Component;
