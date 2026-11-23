import source from '../doc/noi-dung-telco-theo-khung-slide-mau.md?raw'

export const plainText = (text = '') => text.replace(/[`*]/g, '').replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
const lines = (text) => text.split(/\r?\n/).map((line) => line.trim())
const part = (text, title) => text.match(new RegExp(`### ${title}\\r?\\n([\\s\\S]*?)(?=\\n### (?:Bố cục gợi ý|Ghi chú[^\\n]*)|$)`))?.[1].trim() || ''

function tables(text, label) {
  return [...text.matchAll(/(?:^\|[^\n]+\|\r?\n?)+/gm)].map(([block]) => {
    const [header, , ...rows] = lines(block).filter(Boolean).map((line) => line.split('|').slice(1, -1).map((cell) => plainText(cell.trim())))
    return { header, rows, label }
  })
}

const layouts = ['cover', 'roster', 'data', 'attributes', 'encoding', 'smote', 'scaling', 'models', 'training', 'comparison', 'matrix', 'explanation', 'retraining', 'demo', 'closing']
export const slides = [...source.matchAll(/^## Slide (\d+)\. (.+)\r?\n([\s\S]*?)(?=^## |$(?![\s\S]))/gm)].map(([, number, title, text]) => {
  const content = part(text, 'Nội dung trình chiếu')
  return {
    number: Number(number), title, layout: layouts[Number(number) - 1],
    points: lines(content).filter((line) => line.startsWith('- ')).map((line) => line.slice(2)),
    steps: lines(content).filter((line) => /^\d+\. /.test(line)).map((line) => plainText(line.replace(/^\d+\. /, ''))),
    tables: tables(content, title),
    notes: (part(text, 'Ghi chú thuyết trình') || part(text, 'Ghi chú kết thúc') || 'Điền thông tin thực tế của nhóm trước khi báo cáo.').split(/\r?\n\s*\r?\n/).map(plainText),
  }
})

export const sourceName = 'noi-dung-telco-theo-khung-slide-mau.md'
export const coverInfo = slides[0].tables[0].rows[0]
export const comparisonMetrics = slides[9].tables[0]
export const comparisonBest = slides[9].tables[1].header.slice(1).map((_, index) => Math.max(...slides[9].tables[1].rows.map((row) => parseFloat(row[index + 1].replace(',', '.')))))
export const modelIcons = ['tree', 'chart', 'trend']
export const smotePhases = [
  { label: 'Trước SMOTE', stay: 4130, churn: 1495 },
  { label: 'Sau SMOTE', stay: 4130, churn: 4130 },
]
export const importance = [['Hợp đồng theo tháng', 56.61], ['Thời gian sử dụng', 17.93], ['Internet cáp quang', 16.39]]
export const assets = {
  scaling: { file: 'streamlit-chuan-hoa.png', alt: 'Minh họa chuẩn hóa dữ liệu trên ứng dụng Streamlit' },
  explanation: { file: '05_churn_by_Contract.png', alt: 'Tỷ lệ khách rời bỏ theo thời hạn hợp đồng trong dữ liệu Telco' },
}
export const demoCards = [
  { icon: 'chart', title: 'Khám phá dữ liệu' },
  { icon: 'settings', title: 'Huấn luyện và so sánh' },
  { icon: 'users', title: 'Dự đoán khách hàng' },
]
