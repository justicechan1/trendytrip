import { ref } from 'vue'

const isCalendarPopupVisible = ref(false)
const isSearchPopupVisible = ref(false)
const isSavePopupVisible = ref(false)
const isAddPlaceVisible = ref(false)
const isRemovePlaceVisible = ref(false)
const showHashtag = ref(false)


export function usePopup() {

  const closePopups = () => {
    isCalendarPopupVisible.value = false
    isSearchPopupVisible.value = false
    isSavePopupVisible.value = false
    isAddPlaceVisible.value = false
    isRemovePlaceVisible.value = false
    showHashtag.value = false
  }

  const togglePopup = (
    type: 'calendar' | 'search' | 'save' | 'addPlace' | 'removePlace' | 'hashtag'
  ) => {
    if (type === 'hashtag') {
      showHashtag.value = !showHashtag.value
      return
    }

    const mapping = {
      calendar: isCalendarPopupVisible,
      search: isSearchPopupVisible,
      save: isSavePopupVisible,
      addPlace: isAddPlaceVisible,
      removePlace: isRemovePlaceVisible
    }

    const targetRef = mapping[type]
    const wasOpen = targetRef.value

    closePopups()

    if (!wasOpen) {
      targetRef.value = true
    }
  }

  return {
    // state
    isCalendarPopupVisible,
    isSearchPopupVisible,
    isSavePopupVisible,
    isAddPlaceVisible,
    isRemovePlaceVisible,
    showHashtag,
    // actions
    togglePopup,
    closePopups
  }
}
