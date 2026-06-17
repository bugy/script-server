<template>
  <v-list-group :value="group.name">
    <template #activator="{ props }">
      <v-list-item v-bind="props" :title="group.name" class="script-group" />
    </template>
    <ScriptListItem
      v-for="innerScript in group.scripts"
      :key="innerScript.name"
      :script="innerScript"
    />
  </v-list-group>
</template>

<script>
import ScriptListItem from './ScriptListItem';

export default {
  name: 'ScriptListGroup',
  components: {ScriptListItem},
  props: {
    group: {
      type: Object
    }
  }
}
</script>
