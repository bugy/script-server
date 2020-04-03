<template>
    <div class="scripts-list collection" ref="scriptList">
        <template v-for="item in items">
            <ScriptListGroup v-if="item.isGroup" :group="item" :key="item.name" @group-clicked="groupClicked($event)"/>
            <ScriptListItem v-else :script="item" :key="item.name"/>
        </template>
    </div>
</template>

<script>
    import {isBlankString, isEmptyString, isNull, removeElement} from '@/common/utils/common';
    import {mapState} from 'vuex';
    import ScriptListGroup from './ScriptListGroup';
    import ScriptListItem from './ScriptListItem';

    export default {
        name: 'ScriptsList',
        components: {ScriptListGroup, ScriptListItem},
        props: {
            searchText: {
                type: String,
                default: null
            }
        },

        data: function () {
            return {
                activeGroup: null
            }
        },

        computed: {
            ...mapState('scripts', ['scripts', 'selectedScript']),

            items() {
                let groups = this.scripts.filter(script => !isBlankString(script.group))
                    .map(script => script.group)
                    .filter((v, i, a) => a.indexOf(v) === i) // unique elements
                    .map(group => ({name: group, isGroup: true, scripts: [], isActive: this.activeGroup === group}));

                let foundScripts = this.scripts
                    .filter(script =>
                        isEmptyString(this.searchText) || (script.name.toLowerCase().includes(this.searchText.toLowerCase())));

                for (const script of foundScripts.slice()) {
                    if (isBlankString(script.group)) {
                        continue;
                    }
                    let foundGroup = groups.find(g => g.name === script.group);
                    foundGroup.scripts.push(script);
                    removeElement(foundScripts, script);
                }

                const result = foundScripts.concat(groups);
                result.sort((o1, o2) => o1.name.toLowerCase().localeCompare(o2.name.toLowerCase()));

                return result;
            }
        },
        methods: {
            groupClicked(groupName) {
                if (isNull(groupName) || (this.activeGroup === groupName)) {
                    this.activeGroup = null;
                    return;
                }
                this.activeGroup = groupName;
            }
        },
        watch: {
            selectedScript: {
                immediate: true,
                handler(selectedScript) {
                    if (isNull(selectedScript)) {
                        return;
                    }

                    let foundScript = this.scripts.find(script => script.name === selectedScript);
                    if (isNull(foundScript) || isNull(foundScript.group)) {
                        return;
                    }

                    let group = this.items.find(item => item.isGroup && (item.name === foundScript.group));
                    if (isNull(group) || group.isActive) {
                        return;
                    }

                    this.activeGroup = group.name;
                }
            }
        }
    }
</script>

<style scoped>
    .scripts-list {
        overflow: auto;
        overflow-wrap: normal;
        border: none;
        margin: 0;

        flex-grow: 1;
    }

</style>