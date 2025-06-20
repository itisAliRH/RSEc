<script setup lang="ts">
interface Props {
  tool: Tool;
}

const props = defineProps<Props>();

const toolName = computed(() => {
  return getToolName(props.tool);
});
const version = computed(() => {
  return getToolVersion(props.tool);
});
const description = computed(() => {
  return getToolDescription(props.tool);
});
const license = computed(() => {
  return getToolLicense(props.tool);
});
const isFavorite = computed(() => {
  return isToolFavorite(props.tool);
});
const lastUpdate = computed(() => {
  return getToolLastUpdate(props.tool);
});

function toggleFavorite() {
  toggleToolFavorite(props.tool);
}
</script>

<template>
  <UCard :ui="{ body: 'flex h-full flex-col justify-between' }">
    <div>
      <div class="mb-2 break-words">
        <div class="flex items-start justify-between">
          <h3 class="l g:text-2xl mb-1 text-lg font-bold md:text-xl">
            {{ toolName }}
          </h3>

          <UTooltip
            :delay-duration="0"
            :text="isFavorite ? 'Remove from favorites' : 'Add to favorites'"
          >
            <UButton
              :variant="isFavorite ? 'solid' : 'outline'"
              :color="isFavorite ? 'warning' : 'secondary'"
              class="cursor-pointer"
              icon="uil:star"
              @click="toggleFavorite"
            />
          </UTooltip>
        </div>

        <div class="flex flex-wrap gap-2">
          <UBadge icon="uil:box" color="neutral" variant="subtle">
            {{ version }}
          </UBadge>

          <UBadge icon="uil:balance-scale" color="secondary" variant="subtle">
            {{ license }}
          </UBadge>

          <UBadge icon="uil:calendar-alt" variant="subtle">
            {{ lastUpdate }}
          </UBadge>
        </div>
      </div>

      <span>
        {{ description }}
      </span>
    </div>

    <div class="flex justify-end">
      <UTooltip :delay-duration="0" text="View tool details">
        <UButton
          variant="outline"
          color="info"
          icon="uil:info-circle"
          class="mt-4"
          :to="`/tool/${props.tool.tool_name}`"
        >
          View Tool
        </UButton>
      </UTooltip>
    </div>
  </UCard>
</template>
