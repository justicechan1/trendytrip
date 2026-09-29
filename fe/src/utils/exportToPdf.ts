// utils/exportToPdf.ts
import html2pdf from 'html2pdf.js'

export function exportWholePagePdf(fileName = 'full-page.pdf') {
  const el = document.body  // 페이지 전체!

  const opt = {
    margin:       0,
    filename:     fileName,
    image:        { type: 'jpeg', quality: 0.98 },
    html2canvas:  { scale: 2, useCORS: true },
    jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
  }

  html2pdf().set(opt).from(el).save()
}
