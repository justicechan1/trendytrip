// utils/notification.ts
import { toast } from 'vue3-toastify'
import CustomToast from '@/components/ui/toast/CustomToast.vue'

export function notifyUser(message: string, {
  type = 'default',
  duration = 3000,
  actionText,
  onAction
}: {
  type?: 'success' | 'error' | 'info' | 'warning' | 'default',
  duration?: number,
  actionText?: string,
  onAction?: () => void
}) {
  if (actionText && onAction) {
    toast(
      {
        component: CustomToast,
        props: {
          message,
          actionText,
          onAction
        }
      },
      {
        type,
        autoClose: duration
      }
    )
  } else {
    toast(message, {
      type,
      autoClose: duration
    })
  }
}
