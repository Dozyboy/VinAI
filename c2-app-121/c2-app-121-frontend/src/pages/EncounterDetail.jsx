import { useEffect, useState, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import * as encountersApi from '../api/encounters'
import * as clinicalApi from '../api/clinical'
import DashboardLayout from '../components/DashboardLayout'
import './EncounterDetail.css'

const SOAP_TABS = [
  { key: 'subjective', label: 'S - Subjective', fields: [
    { key: 'chief_complaint', label: 'Chief Complaint' },
    { key: 'history', label: 'History' },
    { key: 'review_of_systems', label: 'Review of Systems' },
  ]},
  { key: 'objective', label: 'O - Objective', fields: [
    { key: 'vital_signs', label: 'Vital Signs' },
    { key: 'physical_exam', label: 'Physical Exam' },
    { key: 'lab_results', label: 'Lab Results' },
  ]},
  { key: 'assessment', label: 'A - Assessment', fields: [
    { key: 'diagnosis', label: 'Diagnosis' },
    { key: 'severity', label: 'Severity' },
    { key: 'notes', label: 'Notes' },
  ]},
  { key: 'diagnosis', label: 'D - Diagnosis', fields: [
    { key: 'primary_diagnosis', label: 'Primary Diagnosis' },
    { key: 'differential_diagnoses', label: 'Differential Diagnoses' },
    { key: 'icd_code', label: 'ICD Code' },
  ]},
  { key: 'plan', label: 'P - Plan', fields: [
    { key: 'treatment', label: 'Treatment' },
    { key: 'medications', label: 'Medications' },
    { key: 'follow_up', label: 'Follow-up' },
    { key: 'patient_education', label: 'Patient Education' },
  ]},
]

const AI_STEPS = [
  { key: 'raw', label: '1. Bản ghi thô (ASR)', color: '#6b7280' },
  { key: 'normalized', label: '2. Chuẩn hóa y khoa', color: '#2563eb' },
  { key: 'facts', label: '3. Sự kiện y tế', color: '#7c3aed' },
  { key: 'soap_raw', label: '4. SOAP thô', color: '#0891b2' },
  { key: 'audited', label: '5. SOAP sau audit', color: '#059669' },
]

const sectionApis = {
  subjective: encountersApi.updateSoapSubjective,
  objective: encountersApi.updateSoapObjective,
  assessment: encountersApi.updateSoapAssessment,
  diagnosis: encountersApi.updateSoapDiagnosis,
  plan: encountersApi.updateSoapPlan,
}

const statusLabels = { in_progress: 'Đang khám', completed: 'Hoàn thành', cancelled: 'Đã hủy' }

function parseSoapText(text) {
  if (!text || typeof text !== 'string') {
    if (typeof text === 'object' && text !== null) return text
    return {}
  }

  const trimmed = text.trim()

  try {
    let cleaned = trimmed
      .replace(/```json\s*/gi, '')
      .replace(/```\s*$/gi, '')
      .replace(/^```\s*/gi, '')
      .trim()
    const obj = JSON.parse(cleaned)
    if (typeof obj === 'object' && obj !== null && (obj.subjective || obj.objective || obj.assessment || obj.plan)) {
      return obj
    }
  } catch {}

  const sections = {}
  const patterns = [
    /#\s*(S|Subjective)\s*[-–—]?\s*.*\n([\s\S]*?)(?=\n#\s*(?:O|A|D|P|Objective|Assessment|Diagnosis|Plan)\s|$)/gi,
    /#\s*(O|Objective)\s*[-–—]?\s*.*\n([\s\S]*?)(?=\n#\s*(?:A|D|P|Assessment|Diagnosis|Plan)\s|$)/gi,
    /#\s*(A|Assessment)\s*[-–—]?\s*.*\n([\s\S]*?)(?=\n#\s*(?:D|P|Diagnosis|Plan)\s|$)/gi,
    /#\s*(D|Diagnosis)\s*[-–—]?\s*.*\n([\s\S]*?)(?=\n#\s*(?:P|Plan)\s|$)/gi,
    /#\s*(P|Plan)\s*[-–—]?\s*.*\n([\s\S]*?)$/gi,
  ]

  const map = {
    S: 'subjective', Subjective: 'subjective',
    O: 'objective', Objective: 'objective',
    A: 'assessment', Assessment: 'assessment',
    D: 'diagnosis', Diagnosis: 'diagnosis',
    P: 'plan', Plan: 'plan',
  }

  for (const pattern of patterns) {
    let match
    while ((match = pattern.exec(text)) !== null) {
      const key = match[1]
      const content = match[2].trim()
      if (content && map[key]) {
        sections[map[key]] = content
      }
    }
  }

  if (Object.keys(sections).length === 0) {
    const fallbackSections = text.split(/#\s*[A-Z]\s*[-–—]?\s*/g).filter(Boolean)
    const sectionNames = ['subjective', 'objective', 'assessment', 'diagnosis', 'plan']
    fallbackSections.forEach((content, idx) => {
      if (sectionNames[idx]) sections[sectionNames[idx]] = content.trim()
    })
  }

  if (Object.keys(sections).length === 0) {
    sections.subjective = text
  }
  return sections
}

function hydrateNote(sections) {
  const validKeys = ['subjective', 'objective', 'assessment', 'diagnosis', 'plan']
  const isStructured = typeof sections === 'object' && sections !== null &&
    validKeys.some(k => sections[k] && typeof sections[k] === 'object' && !Array.isArray(sections[k]))

  if (isStructured) {
    const note = {}
    for (const key of validKeys) {
      if (sections[key] && typeof sections[key] === 'object') {
        note[key] = { ...sections[key] }
      } else {
        note[key] = {}
      }
    }
    return note
  }

  const note = {}
  const fieldMap = {
    subjective: ['chief_complaint', 'history', 'review_of_systems'],
    objective: ['vital_signs', 'physical_exam', 'lab_results'],
    assessment: ['diagnosis', 'severity', 'notes'],
    diagnosis: ['primary_diagnosis', 'differential_diagnoses', 'icd_code'],
    plan: ['treatment', 'medications', 'follow_up', 'patient_education'],
  }

  for (const [sec, text] of Object.entries(sections)) {
    note[sec] = {}
    const fields = fieldMap[sec] || []
    if (fields.length > 0) {
      note[sec][fields[0]] = text
      for (let i = 1; i < fields.length; i++) note[sec][fields[i]] = ''
    }
  }
  return note
}

function formatJson(jsonStr) {
  try {
    const obj = typeof jsonStr === 'string' ? JSON.parse(jsonStr) : jsonStr
    return JSON.stringify(obj, null, 2)
  } catch {
    return jsonStr
  }
}

function parseSoapJson(jsonStr) {
  try {
    let obj = typeof jsonStr === 'string' ? jsonStr : jsonStr
    if (typeof obj === 'string') {
      const cleaned = obj
        .replace(/```json\s*/gi, '')
        .replace(/```\s*$/gi, '')
        .replace(/^```\s*/gi, '')
        .trim()
      obj = JSON.parse(cleaned)
      if (typeof obj === 'string') obj = JSON.parse(obj)
    }
    if (typeof obj === 'object' && obj !== null) return obj
  } catch {}
  return null
}

const SOAP_SECTION_META = {
  subjective:    { label: 'S — Subjective',  color: '#6366f1' },
  objective:     { label: 'O — Objective',   color: '#2563eb' },
  assessment:    { label: 'A — Assessment',  color: '#d97706' },
  diagnosis:     { label: 'D — Diagnosis',   color: '#0891b2' },
  plan:          { label: 'P — Plan',        color: '#059669' },
}

function SoapJsonView({ text }) {
  const obj = parseSoapJson(text)
  if (!obj) {
    return <div className="ai-step-text soap-raw">{text}</div>
  }
  return (
    <div className="soap-json-grid">
      {obj.review && (
        <div className="soap-review-card">
          <div className="soap-review-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#d97706" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
            <span>Nhận xét audit</span>
          </div>
          <div className="soap-review-body">{obj.review}</div>
        </div>
      )}
      {Object.entries(SOAP_SECTION_META).map(([key, meta]) => {
        const section = obj[key]
        if (!section || typeof section !== 'object') return null
        const entries = Object.entries(section).filter(([, v]) => v !== undefined && v !== null && v !== '')
        if (entries.length === 0) return null
        return (
          <div key={key} className="fact-card" style={{ '--fact-color': meta.color }}>
            <div className="fact-card-header">
              <span className="fact-card-dot" style={{ background: meta.color }} />
              <span className="fact-card-label">{meta.label}</span>
            </div>
            <div className="fact-card-body">
              <div className="fact-kv">
                {entries.map(([k, v]) => (
                  <div key={k} className="fact-kv-row">
                    <span className="fact-kv-key">{formatLabel(k)}</span>
                    <span className="fact-kv-value">{String(v)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

function parseFacts(jsonStr) {
  try {
    let obj = typeof jsonStr === 'string' ? jsonStr : jsonStr
    if (typeof obj === 'string') {
      const cleaned = obj
        .replace(/```json\s*/gi, '')
        .replace(/```\s*$/gi, '')
        .replace(/^```\s*/gi, '')
        .trim()
      obj = JSON.parse(cleaned)
      if (typeof obj === 'string') obj = JSON.parse(obj)
    }
    return obj
  } catch {
    return null
  }
}

function formatLabel(key) {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
}

const FACT_SECTIONS = [
  { key: 'patient_info', label: 'Thông tin bệnh nhân', color: '#6366f1' },
  { key: 'chief_complaint', label: 'Lý do khám', color: '#d97706' },
  { key: 'symptoms', label: 'Triệu chứng', color: '#dc2626' },
  { key: 'vital_signs', label: 'Dấu hiệu sinh tồn', color: '#059669' },
  { key: 'physical_exam', label: 'Khám lâm sàng', color: '#2563eb' },
  { key: 'lab_results', label: 'Xét nghiệm', color: '#7c3aed' },
  { key: 'diagnosis', label: 'Chẩn đoán', color: '#0891b2' },
  { key: 'medications', label: 'Thuốc kê', color: '#ea580c' },
  { key: 'procedures', label: 'Thủ thuật / XN chỉ định', color: '#4f46e5' },
  { key: 'follow_up', label: 'Tái khám', color: '#059669' },
  { key: 'additional_notes', label: 'Ghi chú khác', color: '#6b7280' },
]

function FactTag({ text }) {
  return <span className="fact-tag">{text}</span>
}

function FactCard({ section, value }) {
  if (!value || (Array.isArray(value) && value.length === 0)) return null
  if (typeof value === 'string' && !value.trim()) return null

  const renderContent = () => {
    if (Array.isArray(value)) {
      const filtered = value.filter(v => v && v !== '')
      if (filtered.length === 0) return null
      return (
        <div className="fact-tags">
          {filtered.map((item, i) => <FactTag key={i} text={item} />)}
        </div>
      )
    }

    if (typeof value === 'object' && value !== null) {
      const entries = Object.entries(value).filter(([, v]) => {
        if (v === null || v === undefined || v === '') return false
        if (Array.isArray(v) && v.length === 0) return false
        if (typeof v === 'object' && Object.keys(v).length === 0) return false
        return true
      })
      if (entries.length === 0) return null
      return (
        <div className="fact-kv">
          {entries.map(([k, v]) => {
            let display = String(v)
            if (Array.isArray(v)) {
              display = v.join(', ')
            } else if (typeof v === 'object' && v !== null) {
              display = Object.entries(v).map(([ak, av]) => `${formatLabel(ak)}: ${av}`).join(', ')
            }
            return (
              <div key={k} className="fact-kv-row">
                <span className="fact-kv-key">{formatLabel(k)}</span>
                <span className="fact-kv-value">{display}</span>
              </div>
            )
          })}
        </div>
      )
    }

    return <span className="fact-text">{String(value)}</span>
  }

  const content = renderContent()
  if (!content) return null

  return (
    <div className="fact-card" style={{ '--fact-color': section.color }}>
      <div className="fact-card-header">
        <span className="fact-card-dot" style={{ background: section.color }} />
        <span className="fact-card-label">{section.label}</span>
      </div>
      <div className="fact-card-body">
        {content}
      </div>
    </div>
  )
}

export default function EncounterDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const fileInputRef = useRef(null)
  const [encounter, setEncounter] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('subjective')
  const [saving, setSaving] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [aiResult, setAiResult] = useState(null)
  const [activeAiStep, setActiveAiStep] = useState('raw')

  const load = useCallback(() => {
    encountersApi.getById(id)
      .then(setEncounter)
      .catch(() => navigate('/encounters'))
      .finally(() => setLoading(false))
  }, [id])

  useEffect(() => { load() }, [load])

  const soapNote = encounter?.soap_notes?.[0]
  const noteId = soapNote?.id

  async function handleSaveSection(sectionKey) {
    const section = soapNote?.[sectionKey]
    if (!noteId || !section) return
    setSaving(sectionKey)
    try {
      await sectionApis[sectionKey](id, noteId, section)
      await load()
    } catch (err) { alert(err.message) }
    finally { setSaving(null) }
  }

  function updateField(sectionKey, fieldKey, value) {
    setEncounter(prev => {
      const notes = [...(prev.soap_notes || [])]
      const note = { ...notes[0] }
      note[sectionKey] = { ...(note[sectionKey] || {}), [fieldKey]: value }
      notes[0] = note
      return { ...prev, soap_notes: notes }
    })
  }

  async function handleGenerate() {
    if (!selectedFile) return
    setGenerating(true)
    setAiResult(null)
    try {
      const res = await clinicalApi.generateSoapNote(selectedFile)
      setAiResult({
        raw: res.transcript,
        normalized: res.normalized_transcript,
        facts: res.facts,
        soap_raw: res.soap_note,
        audited: res.audited_soap,
      })
      setActiveAiStep('raw')

      const sections = parseSoapText(res.audited_soap)
      const hydrated = hydrateNote(sections)

      let createdNoteId = noteId
      if (!createdNoteId) {
        const created = await encountersApi.createSoapNote(id, {
          note_type: 'initial',
          subjective: hydrated.subjective || {},
          objective: hydrated.objective || {},
          assessment: hydrated.assessment || {},
          diagnosis: hydrated.diagnosis || {},
          plan: hydrated.plan || {},
        })
        createdNoteId = created.id
      } else {
        for (const [sec, data] of Object.entries(hydrated)) {
          if (data && Object.values(data).some(v => v)) {
            try { await sectionApis[sec](id, createdNoteId, data) } catch {}
          }
        }
      }

      await load()
    } catch (err) { alert(err.message) }
    finally { setGenerating(false) }
  }

  async function handleComplete() {
    if (!window.confirm('Xác nhận kết thúc lượt khám? Bác sĩ sẽ không thể chỉnh sửa SOAP note sau khi hoàn thành.')) return
    try {
      await encountersApi.update(id, { status: 'completed' })
      await load()
    } catch (err) { alert(err.message) }
  }

  if (loading) return <DashboardLayout><div className="ed-loading">Đang tải…</div></DashboardLayout>
  if (!encounter) return null

  const isCompleted = encounter.status === 'completed'

  return (
    <DashboardLayout>
      <div className="ed-wrap">
        <div className="ed-topbar">
          <button className="btn-ghost-sm" onClick={() => navigate('/encounters')}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
            Quay lại
          </button>
          <span className="ed-status" style={{ background: (encounter.status === 'in_progress' ? '#d97706' : '#059669') + '18', color: encounter.status === 'in_progress' ? '#d97706' : '#059669' }}>
            {statusLabels[encounter.status] || encounter.status}
          </span>
        </div>

        <div className="ed-header">
          <div className="ed-patient">
            <div className="ed-avatar">{encounter.patient?.full_name?.charAt(0) || '?'}</div>
            <div>
              <h1>{encounter.patient?.full_name}</h1>
              <p>Mã BN: {encounter.patient?.medical_record_no || '—'} · {encounter.patient?.gender === 'male' ? 'Nam' : encounter.patient?.gender === 'female' ? 'Nữ' : '—'}</p>
            </div>
          </div>
          <div className="ed-meta">
            <div className="ed-meta-item">
              <span className="ed-meta-label">Bác sĩ</span>
              <span>{encounter.doctor?.full_name}</span>
            </div>
            <div className="ed-meta-item">
              <span className="ed-meta-label">Chuyên khoa</span>
              <span>{encounter.doctor?.specialization || '—'}</span>
            </div>
            <div className="ed-meta-item">
              <span className="ed-meta-label">Ngày khám</span>
              <span>{encounter.encounter_date}</span>
            </div>
            <div className="ed-meta-item">
              <span className="ed-meta-label">Chief complaint</span>
              <span>{encounter.chief_complaint || '—'}</span>
            </div>
          </div>
        </div>

        {!isCompleted && (
          <div className="ed-recording-box">
            <div className="ed-recording-header">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
              <div>
                <h3>Ghi âm khám bệnh</h3>
                <p>Chọn file ghi âm (mp3, wav, m4a, ogg) để AI tự động tạo SOAP note</p>
              </div>
            </div>

            <div className="ed-recording-upload">
              <input
                ref={fileInputRef}
                type="file"
                accept=".mp3,.wav,.m4a,.ogg,.flac,.webm"
                onChange={e => setSelectedFile(e.target.files[0])}
                hidden
              />
              <button className="btn-upload" onClick={() => fileInputRef.current?.click()}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                {selectedFile ? selectedFile.name : 'Chọn file ghi âm'}
              </button>
              <button className="btn-gen" onClick={handleGenerate} disabled={!selectedFile || generating}>
                {generating ? (
                  <>Đang xử lý…</>
                ) : (
                  <><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="22 3 11 8 12 12 16 16 11 21 8 13 3 22 22 3"/></svg>Tạo SOAP note</>
                )}
              </button>
            </div>

            {aiResult && (
              <div className="ai-pipeline">
                <div className="ai-pipeline-header">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
                  <span>Kết quả AI Pipeline</span>
                </div>

                <div className="ai-steps">
                  {AI_STEPS.map(step => (
                    <button
                      key={step.key}
                      className={`ai-step-btn${activeAiStep === step.key ? ' active' : ''}`}
                      onClick={() => setActiveAiStep(step.key)}
                      style={{ '--step-color': step.color }}
                    >
                      <span className="ai-step-dot" style={{ background: step.color }} />
                      {step.label}
                    </button>
                  ))}
                </div>

                <div className="ai-step-content">
                  {activeAiStep === 'raw' && (
                    <div className="ai-step-panel">
                      <div className="ai-step-label">Transcript thô từ ASR (PhoWhisper)</div>
                      <div className="ai-step-text">{aiResult.raw}</div>
                    </div>
                  )}
                  {activeAiStep === 'normalized' && (
                    <div className="ai-step-panel">
                      <div className="ai-step-label">Transcript sau chuẩn hóa y khoa & sửa lỗi chính tả</div>
                      <div className="ai-step-text normalized">{aiResult.normalized}</div>
                    </div>
                  )}
                  {activeAiStep === 'facts' && (
                    <div className="ai-step-panel">
                      <div className="ai-step-label">Sự kiện y tế được trích xuất</div>
                      <div className="facts-grid">
                        {(() => {
                          const factsObj = parseFacts(aiResult.facts)
                          if (!factsObj) {
                            return <div className="facts-empty">Không có dữ liệu</div>
                          }
                          return FACT_SECTIONS.map(section => (
                            <FactCard key={section.key} section={section} value={factsObj[section.key]} />
                          ))
                        })()}
                      </div>
                    </div>
                  )}
                  {activeAiStep === 'soap_raw' && (
                    <div className="ai-step-panel">
                      <div className="ai-step-label">SOAP Note thô từ generate_soap</div>
                      <SoapJsonView text={aiResult.soap_raw} />
                    </div>
                  )}
                  {activeAiStep === 'audited' && (
                    <div className="ai-step-panel">
                      <div className="ai-step-label">SOAP Note sau khi audit (final)</div>
                      <SoapJsonView text={aiResult.audited} />
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {encounter.recordings?.length > 0 && (
          <div className="ed-recordings">
            <h3>Ghi âm đã lưu ({encounter.recordings.length})</h3>
            {encounter.recordings.map((r, i) => (
              <div key={i} className="ed-recording-item">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg>
                <span>Ghi âm {i + 1}</span>
              </div>
            ))}
          </div>
        )}

        {soapNote && (
          <>
            <div className="ed-tabs">
              {SOAP_TABS.map(tab => {
                const hasData = soapNote[tab.key] && Object.values(soapNote[tab.key]).some(v => v)
                return (
                  <button key={tab.key} className={`ed-tab${activeTab === tab.key ? ' active' : ''}${hasData ? ' has-data' : ''}`} onClick={() => setActiveTab(tab.key)}>
                    {tab.label}
                  </button>
                )
              })}
            </div>

            <div className="ed-section">
              {SOAP_TABS.find(t => t.key === activeTab)?.fields.map(field => {
                const value = soapNote[activeTab]?.[field.key] || ''
                return (
                  <div key={field.key} className="ed-field">
                    <label>{field.label}</label>
                    {isCompleted ? (
                      <div className="ed-field-value">{value || '—'}</div>
                    ) : (
                      <textarea
                        rows={4}
                        value={value}
                        onChange={e => updateField(activeTab, field.key, e.target.value)}
                        placeholder={`Nhập ${field.label.toLowerCase()}...`}
                      />
                    )}
                  </div>
                )
              })}

              {!isCompleted && (
                <div className="ed-section-actions">
                  <button className="btn-primary" onClick={() => handleSaveSection(activeTab)} disabled={saving === activeTab}>
                    {saving === activeTab ? 'Đang lưu…' : `Lưu ${SOAP_TABS.find(t => t.key === activeTab)?.label}`}
                  </button>
                </div>
              )}
            </div>
          </>
        )}

        {!isCompleted && (
          <div className="ed-complete">
            <button className="btn-complete" onClick={handleComplete}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              Kết thúc lượt khám
            </button>
          </div>
        )}

        {isCompleted && (
          <div className="ed-completed-banner">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            Lượt khám đã hoàn thành. SOAP note đã được lưu vào hồ sơ.
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
