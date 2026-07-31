import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import './Home.css'

export default function Home() {
  return (
    <>
      <Navbar />
      <main className="home">
        <section className="hero-section">
          <div className="hero-badge">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            Giải pháp AI cho lâm sàng
          </div>

          <h1 className="hero-title">
            Chuyển giọng nói khám bệnh<br />
            <span className="gradient-text">thành ghi chú lâm sàng</span>
          </h1>

          <p className="hero-desc">
            Trợ lý AI ghi âm hội thoại khám bệnh, tự động tạo SOAP note có cấu trúc
            bằng tiếng Việt — giúp bác sĩ tiết kiệm thời gian, tập trung vào bệnh nhân.
          </p>

          <div className="hero-actions">
            <Link to="/login" className="btn-hero btn-hero-primary">
              Bắt đầu dùng thử
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            </Link>
            <a href="#how-it-works" className="btn-hero btn-hero-secondary">
              Tìm hiểu thêm
            </a>
          </div>
        </section>

        <section id="how-it-works" className="steps-section">
          <h2 className="section-title">Cách hoạt động</h2>
          <p className="section-desc">Ba bước đơn giản để tạo ghi chú lâm sàng</p>

          <div className="steps-grid">
            <div className="step-card">
              <div className="step-number">1</div>
              <div className="step-icon">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
              </div>
              <h3>Ghi âm hội thoại</h3>
              <p>Bác sĩ bắt đầu ghi âm buổi khám sau khi có đồng thuận từ bệnh nhân. Hệ thống ghi lại toàn bộ hội thoại tự nhiên.</p>
            </div>

            <div className="step-card">
              <div className="step-number">2</div>
              <div className="step-icon">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
              </div>
              <h3>AI xử lý & sinh SOAP</h3>
              <p>ASR y tế chuyển giọng nói thành văn bản, LLM phân tích và tạo SOAP note có cấu trúc (Subjective, Objective, Assessment, Plan).</p>
            </div>

            <div className="step-card">
              <div className="step-number">3</div>
              <div className="step-icon">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
              </div>
              <h3>Rà soát & duyệt</h3>
              <p>Bác sĩ kiểm tra, chỉnh sửa ghi chú trước khi lưu vào hồ sơ bệnh án điện tử (EMR). Không tự động chốt chẩn đoán.</p>
            </div>
          </div>
        </section>

        <section className="features-section">
          <h2 className="section-title">Tính năng nổi bật</h2>

          <div className="features-grid">
            <div className="feature-item">
              <div className="feature-icon" style={{ background: 'var(--primary-light)' }}>
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              </div>
              <div>
                <h4>Bảo mật & mã hóa</h4>
                <p>Dữ liệu âm thanh được mã hóa đầu cuối, tự động xóa theo chính sách.</p>
              </div>
            </div>

            <div className="feature-item">
              <div className="feature-icon" style={{ background: '#fef3c7' }}>
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#d97706" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
              </div>
              <div>
                <h4>Đồng thuận ghi âm</h4>
                <p>Bắt buộc xin phép bệnh nhân trước khi ghi âm, đảm bảo tuân thủ quy định.</p>
              </div>
            </div>

            <div className="feature-item">
              <div className="feature-icon" style={{ background: '#d1fae5' }}>
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#059669" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
              </div>
              <div>
                <h4>SOAP note tiếng Việt</h4>
                <p>Ghi chú lâm sàng có cấu trúc bằng tiếng Việt, phù hợp với quy trình y tế.</p>
              </div>
            </div>

            <div className="feature-item">
              <div className="feature-icon" style={{ background: '#ede9fe' }}>
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
              </div>
              <div>
                <h4>Giao diện review</h4>
                <p>Bác sĩ rà soát, chỉnh sửa trước khi duyệt — kiểm soát hoàn toàn nội dung.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="cta-section">
          <div className="cta-card">
            <h2>Sẵn sàng trải nghiệm?</h2>
            <p>Dùng thử miễn phí — không cần thẻ tín dụng.</p>
            <Link to="/login" className="btn-hero btn-hero-primary">
              Đăng nhập ngay
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            </Link>
          </div>
        </section>

        <footer className="footer">
          <p>&copy; 2026 Ambient Scribe. Bảo mật dữ liệu y tế là ưu tiên hàng đầu.</p>
        </footer>
      </main>
    </>
  )
}
