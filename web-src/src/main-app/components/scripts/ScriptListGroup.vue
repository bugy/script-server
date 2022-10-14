<template>
  <div :class="{active:group.isActive}" class="script-list-group">
    <a :key="group.name"
       class="collection-item waves-effect script-group"
       @click="$emit('group-clicked', group.name)">
      <span>{{ group.name }}</span>
      <i class="material-icons">
        {{ group.isActive ? 'expand_less' : 'expand_more' }}
      </i>
    </a>

    <ScriptListItem v-for="innerScript in group.scripts"
                    v-if="group.isActive" :key="innerScript.name"
                    :script="innerScript"/>
  </div>
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

<style scoped>
  @import "./ScriptListGroup.css";
</style>