import script from '../doc/kich-ban-thuyet-trinh-telco-churn.md?raw'

const sections = script.trimEnd().split(/^## /m)
const plainText = (value) => value
  .replaceAll('**', '')
  .replaceAll('`', '')
  .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')

const field = (section, label) => {
  const prefix = `**${label}** · `
  const line = section.split(/\r?\n/).find((entry) => entry.startsWith(prefix))
  return plainText(line?.slice(prefix.length).trim() ?? '')
}

const quotes = (section) => section.split(/\r?\n/)
  .filter((line) => line.startsWith('> '))
  .map((line) => plainText(line.slice(2)))

const firstTable = (section, label) => {
  const lines = section.match(/^\|[^\r\n]+/gm)
  if (!lines?.length) return undefined
  const [header, , ...rows] = lines.map((line) => line.split('|').slice(1, -1)
    .map((cell) => plainText(cell.trim())))
  return { header, rows, label }
}

const scriptSlides = sections.flatMap((section) => {
  const heading = section.match(/^Slide (\d+) · (.+)/)
  if (!heading) return []

  const [, number, title] = heading
  const [, alt, imageFile] = section.match(/^!\[([^\]]+)\]\(\.\.\/images\/([^/)]+)\)/m) ?? []
  return [{
    number: Number(number),
    title,
    text: section,
    image: imageFile ? { file: imageFile, alt } : undefined,
    notes: {
      duration: field(section, 'Thời lượng'),
      cue: field(section, 'Trên slide'),
      paragraphs: quotes(section),
      transition: field(section, 'Chuyển ý'),
    },
  }]
})

const findSection = (title) => sections.find((section) => section.startsWith(title))
const comparison = firstTable(scriptSlides[9].text, 'So sánh mô hình trên tập kiểm thử')
const comparisonBest = comparison.header.slice(1).map((_, column) =>
  Math.max(...comparison.rows.map((row) => parseFloat(row[column + 1].replace(',', '.')))),
)

export const courseName = field(sections[0], 'Môn học')
export const coverInfo = [
  ['Nhóm', field(sections[0], 'Nhóm')],
  ['Giảng viên hướng dẫn', field(sections[0], 'Giảng viên hướng dẫn')],
]

const content = [
  {
    section: 'Mở đầu', nav: 'Bài toán rời bỏ', type: 'cover',
    lead: 'Đội chăm sóc nên xem hồ sơ nào trước?',
  },
  {
    section: 'Mở đầu', nav: 'Thành viên và phân công', type: 'table',
    table: firstTable(scriptSlides[1].text, 'Thành viên nhóm và nhiệm vụ'),
  },
  {
    section: 'Dữ liệu', nav: 'Chất lượng dữ liệu',
    metrics: [['7.043', 'Hồ sơ ban đầu'], ['7.032', 'Hồ sơ hợp lệ'], ['26,58%', 'Khách rời bỏ']],
    detail: 'Loại 11 hồ sơ thiếu TotalCharges. Sau làm sạch có 5.163 khách ở lại và 1.869 khách rời bỏ.',
  },
  {
    section: 'Dữ liệu', nav: 'Thuộc tính và tỷ lệ Churn',
    table: firstTable(scriptSlides[3].text, 'Các thuộc tính chính của IBM Telco'),
    detail: '1.655 trong 3.875 khách hợp đồng theo tháng đã rời bỏ (42,7%).',
  },
  {
    section: 'Tiền xử lý', nav: 'Mã hóa và chia tập', layout: 'wide',
    lead: 'Mã hóa Churn thành 0/1 và tạo cột chỉ báo cho loại hợp đồng. Chia phân tầng 80/20 với seed 42.',
    table: firstTable(scriptSlides[4].text, 'Kết quả khảo sát từng đặc trưng'),
  },
  {
    section: 'Tiền xử lý', nav: 'Cân bằng bằng SMOTE', layout: 'wide',
    lead: 'SMOTE sinh 2.635 mẫu rời bỏ trong tập huấn luyện. Hai lớp đạt 4.130 mẫu mỗi lớp, còn tập kiểm thử giữ 1.407 hồ sơ.',
  },
  {
    section: 'Tiền xử lý', nav: 'Chuẩn hóa đặc trưng', layout: 'wide',
    formula: 'z = (x − μ) / σ',
    detail: 'Bảng minh họa trên tập huấn luyện gốc. Pipeline Logistic khớp scaler sau SMOTE.',
  },
  {
    section: 'Mô hình', nav: 'Cây quyết định và Logistic',
    points: [
      ['Cây quyết định', '7 đặc trưng, tiêu chí Gini và độ sâu tối đa 4. Nút gốc xét hợp đồng theo tháng.'],
      ['Hồi quy Logistic', 'Bản đầy đủ có 23 đặc trưng. Bản điều chỉnh dùng 16 đặc trưng từ 12 trường gốc và ngưỡng phân loại 0,5.'],
    ],
  },
  {
    section: 'Mô hình', nav: 'Huấn luyện và độ đo',
    points: [
      ['Huấn luyện Logistic', 'SMOTE → StandardScaler → Logistic. Kiểm định chéo phân tầng 5 lượt, sau đó huấn luyện lại trên toàn bộ tập train.'],
      ['Recall', 'Tỷ lệ phát hiện trong số khách thực sự rời bỏ.'],
      ['Precision', 'Tỷ lệ khách thực sự rời bỏ trong số hồ sơ được cảnh báo.'],
    ],
  },
  {
    section: 'Kết quả', nav: 'So sánh mô hình', type: 'comparison',
    lead: 'Cả ba cấu hình được đánh giá trên cùng 1.407 hồ sơ.',
    table: comparison,
    best: comparisonBest,
  },
  {
    section: 'Kết quả', nav: 'Ma trận nhầm lẫn', layout: 'wide',
    metrics: [['76,2%', 'Recall · 285/374 · 89 bỏ sót'], ['50,5%', 'Precision · 285/564 · 279 cảnh báo nhầm']],
  },
  {
    section: 'Kết quả', nav: 'Hệ số Logistic',
    table: firstTable(scriptSlides[11].text, 'Các hệ số Logistic tiêu biểu'),
    detail: 'Dấu của hệ số cho biết chiều thay đổi log-odds rời bỏ dự đoán khi giữ các biến còn lại cố định.',
  },
  {
    section: 'Ứng dụng', nav: 'Huấn luyện theo đợt', type: 'process',
    steps: ['Dữ liệu', 'Tiền xử lý', 'Huấn luyện', 'So sánh', 'Dự đoán'],
    points: [
      ['Cập nhật dữ liệu', 'Bổ sung CSV đã có nhãn Churn. Khi mã khách trùng, ưu tiên bản ghi mới.'],
      ['Chọn mô hình', 'Lưu từng lần chạy, đối chiếu Recall hoặc F1 và chọn mô hình dùng ở bước Dự đoán.'],
    ],
  },
  {
    section: 'Ứng dụng', nav: 'Demo Streamlit', type: 'demo',
    scenes: [
      { label: 'Dữ liệu', image: scriptSlides[2].image, action: 'Mô tả dữ liệu', result: 'Sau khi loại 11 hồ sơ thiếu tổng phí, còn 7.032 hồ sơ.' },
      { label: 'Đánh giá', image: scriptSlides[10].image, action: 'Kỹ thuật khai phá', result: 'Logistic điều chỉnh phát hiện 285 ca và bỏ sót 89 ca rời bỏ.' },
      { label: 'Dự đoán', image: scriptSlides[13].image, action: 'Chạy thử 3 khách hàng mẫu', result: 'Dashboard xếp hồ sơ theo điểm rủi ro từ cao xuống thấp.' },
    ],
    rows: [
      ['DEMO001', '0,9120', 'Rời bỏ', 'Cao'],
      ['DEMO003', '0,4634', 'Ở lại', 'Trung bình'],
      ['DEMO002', '0,0131', 'Ở lại', 'Thấp'],
    ],
  },
  {
    section: 'Kết luận', nav: 'Tổng kết và hỏi đáp', type: 'closing',
    metrics: [
      ['42,7%', 'Tỷ lệ rời bỏ ở nhóm hợp đồng theo tháng'],
      ['285/374', 'Khách rời bỏ được Logistic điều chỉnh phát hiện'],
      ['279', 'Cảnh báo nhầm trên cùng tập kiểm thử'],
    ],
    detail: 'Dashboard dùng điểm để xếp ưu tiên. Trước khi vận hành, cần đánh giá trên dữ liệu mới và chọn ngưỡng phù hợp với nguồn lực rà soát.',
  },
]

export const slides = scriptSlides.map(({ text, ...slide }) => ({
  type: 'evidence',
  ...content[slide.number - 1],
  ...slide,
}))

const demo = scriptSlides[13]
export const demoSteps = firstTable(demo.text).rows
export const demoNotes = demo.notes.paragraphs[0]
export const demoPreparation = field(demo.text, 'Chuẩn bị')

const retraining = findSection('Phần dự phòng · Demo huấn luyện lại')
export const retrainingSteps = Array.from(retraining.matchAll(/^\d+\. (.+)/gm), ([, step]) => plainText(step))
export const questions = firstTable(findSection('Câu hỏi phản biện dự kiến')).rows

const ols = findSection('Phần dự phòng · Hồi quy tuyến tính')
export const olsNotes = {
  table: firstTable(ols, 'Kết quả hồi quy tuyến tính về phí hàng tháng'),
  paragraphs: ols.split(/\r?\n/).slice(1).filter((line) => line.trim() && !line.startsWith('|')).map(plainText),
}
