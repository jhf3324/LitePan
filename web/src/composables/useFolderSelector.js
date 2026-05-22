import { useModal } from './useModal'
import FolderSelectorModal from '../components/common/FolderSelectorModal.vue'

export function useFolderSelector() {
  const { custom } = useModal()

  const selectFolder = async (accountId, options = {}) => {
    return await custom({
      title: '',
      size: null,
      closable: false,
      hideFooter: true,
      modalClass: 'modal-folder-selector',
      bodyClass: 'modal-body-flush',
      component: FolderSelectorModal,
      componentProps: {
        accountId,
        ...options
      },
      ...options.modalOptions
    })
  }

  return {
    selectFolder
  }
}
