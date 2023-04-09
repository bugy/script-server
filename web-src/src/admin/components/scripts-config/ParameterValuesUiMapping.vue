<template>
  <div class="parameter-values-ui-mapping">
    <p>
      Optional mapping for values (defined above), which is shown to users.
      You can use this feature to show accepted script values in a more human readable form.
    </p>
    <div v-for="mapping in mappings" class="row s12">
      <Textfield
          v-model="mapping['script_value']"
          :config="{'name': 'Script value'}"
          class="inline col s6 l4 m6"/>
      <Textfield
          v-model="mapping['ui_value']"
          :config="{'name': 'UI value'}"
          class="inline col s6 l4 m6"/>
    </div>

  </div>
</template>

<script>
import Textfield from '@/common/components/textfield.vue';
import {forEachKeyValue, isBlankString, isNull} from '@/common/utils/common';

export default {
  name: 'ParameterValuesUiMapping',
  components: {Textfield},
  props: {
    value: {
      type: Object,
      default: () => {
      }
    }
  },
  data() {
    return {
      mappings: []
    }
  },
  mounted() {

  },
  watch: {
    value: {
      immediate: true,
      handler(config) {
        forEachKeyValue(config, (key, value) => {
          let found = false;
          let emptyMapping = null;

          for (const localMapping of this.mappings) {
            const scriptValue = localMapping['script_value']
            const uiValue = localMapping['ui_value']

            if (scriptValue.trim() === key.trim()) {
              localMapping['ui_value'] = value
              found = true
              break
            }

            if (isBlankString(scriptValue) && isBlankString(uiValue)) {
              emptyMapping = localMapping
            }
          }

          if (!found) {
            if (isNull(emptyMapping)) {
              emptyMapping = {}
              this.mappings.push(emptyMapping)
            }

            emptyMapping['script_value'] = key;
            emptyMapping['ui_value'] = value;
          }
        })
      }
    },
    mappings: {
      deep: true,
      immediate: true,
      handler(newMappings) {
        const newValue = {}
        let hasEmpty = false

        for (const mapping of newMappings) {
          const scriptValue = mapping['script_value'];
          const uiValue = mapping['ui_value'];

          if (isBlankString(scriptValue) && isBlankString(uiValue)) {
            hasEmpty = true
            continue
          }

          newValue[scriptValue] = uiValue
        }

        if (!hasEmpty) {
          this.mappings.push({'script_value': '', 'ui_value': ''})
        }

        this.$emit('input', newValue);
      }
    }
  }
}
</script>

<style scoped>

</style>