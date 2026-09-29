// utils/exportToHtml.ts
export function exportWholePageHtml(fileName = 'page.html') {
  const htmlContent = `
    <!DOCTYPE html>
    <html lang="ko">
      <head>
        <meta charset="UTF-8">
        <title>저장된 페이지</title>
        <style>
          body {
            font-family: sans-serif;
            padding: 20px;
          }
        </style>
      </head>
      <body>
        ${document.body.innerHTML}
      </body>
    </html>
  `

  const blob = new Blob([htmlContent], { type: 'text/html' })
  const url = URL.createObjectURL(blob)

  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  a.click()

  URL.revokeObjectURL(url)
}
