import script from '../doc/kich-ban.md?raw'

const sections = script.trimEnd().split(/^## /m)
const plainText = (value) => value
  .replace(/[\x60*]/g, '')
  .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')

const linesOf = (section) => section?.split(/\r?\n/).map((line) => line.trim()) ?? []
const part = (section, heading) => section.split(/^### /m)
  .find((entry) => entry.startsWith(heading + '\r\n') || entry.startsWith(heading + '\n')) ?? ''
const field = (section, label) => {
  const prefix = `**${label}:** `
  const line = linesOf(section).find((entry) => entry.startsWith(prefix))
  return plainText(line?.slice(prefix.length) ?? '')
}
const quotes = (section) => linesOf(section).filter((line) => line.startsWith('> '))
  .map((line) => plainText(line.slice(2)))
const bullets = (section) => linesOf(section).filter((line) => line.startsWith('- '))
  .map((line) => line.slice(2))

function readTable(section, label) {
  const lines = linesOf(section).filter((line) => line.startsWith('|'))
  if (!lines.length) return undefined
  const [header, , ...rows] = lines.map((line) => line.split('|').slice(1, -1)
    .map((cell) => plainText(cell.trim())))
  return { header, rows, label }
}

const layouts = [
  ['Mở đầu', 'cover'],
  ['Mở đầu', 'roster'],
  ['Dữ liệu', 'quality'],
  ['Dữ liệu', 'attributes'],
  ['Tiền xử lý', 'encoding'],
  ['Tiền xử lý', 'smote'],
  ['Tiền xử lý', 'scaling'],
  ['Mô hình', 'models'],
  ['Mô hình', 'training'],
  ['Kết quả', 'comparison'],
  ['Kết quả', 'matrix'],
  ['Kết quả', 'coefficients'],
  ['Ứng dụng', 'retraining'],
  ['Ứng dụng', 'demo'],
  ['Kết luận', 'closing'],
]

export const slides = sections.flatMap((section) => {
  const heading = section.match(/^Slide (\d+) · (.+)/)
  if (!heading) return []

  const [, number, title] = heading
  const [chapter, layout] = layouts[Number(number) - 1]
  const content = part(section, 'Nội dung để chiếu')
  const [, alt, file] = part(section, 'Ảnh và bố cục').match(/^!\[([^\]]+)\]\(\.\.\/images\/([^/)]+)\)/m) ?? []
  const statements = linesOf(content).slice(1).filter((line) => line.startsWith('**')).map(plainText)
  return [{
    title,
    chapter,
    layout,
    statements,
    points: bullets(content),
    table: readTable(content, title),
    image: file ? { file, alt } : undefined,
    notes: {
      duration: field(section, 'Thời lượng'),
      paragraphs: quotes(part(section, 'Lời thoại')),
      transition: field(section, 'Chuyển ý'),
    },
  }]
})

export const coverFlow = ['Hồ sơ khách hàng', 'Mô hình phân loại', 'Điểm nguy cơ và nhãn Churn']
export const coverInfo = slides[0].statements[1].split(' · ').map((item) => item.split(': '))
export const dataSource = 'https://github.com/IBM/telco-customer-churn-on-icp4d/blob/master/data/Telco-Customer-Churn.csv'

const comparison = slides.find((slide) => slide.layout === 'comparison').table
export const comparisonBest = comparison.header.slice(1).map((_, column) =>
  Math.max(...comparison.rows.map((row) => parseFloat(row[column + 1].replace(',', '.')))),
)

const demoSection = sections.find((section) => section.startsWith('Slide 14 ·'))
const demoSpeech = part(demoSection, 'Trình tự thao tác và lời thoại')
export const demoPreparation = bullets(part(demoSection, 'Chuẩn bị trước khi báo cáo')).map(plainText)
export const demoSteps = readTable(demoSpeech).rows
export const demoFallback = quotes(demoSpeech)
export const questions = readTable(sections.find((section) => section.startsWith('Ghi chú phản biện'))).rows
