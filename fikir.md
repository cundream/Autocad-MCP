# AutoCAD MCP Pro — Geliştirme Fikirleri

> **Proje:** autocad-mcp-pro v1.0.0  
> **Tarih:** 5 Mart 2026  
> **Durum:** 67 tool, 6 resource, 5 prompt — FastMCP 3.0 + Dual Backend (COM + ezdxf)

---

## Mevcut Durum Özeti

| Alan | Durum |
|------|-------|
| Tool sayısı | 67 |
| Resource sayısı | 6 |
| Prompt sayısı | 5 |
| Backend | COM (Windows) + ezdxf (cross-platform) |
| Test | 17 test (sadece ezdxf backend) |
| Coverage aracı | Yok |
| CI/CD | Yok |
| README.md | Eksik |
| Auth | Yok |
| Lint/Format | Konfigüre edilmemiş |

---

## 1. GÜVENLİK — Kritik Öncelik

### 1.1 Path Traversal Koruması

**Sorun:** `drawing_open`, `drawing_save`, `drawing_save_as`, `drawing_export_pdf` gibi tool'lar doğrudan kullanıcı path'i alıyor. `..` veya mutlak path kontrolü yok.

**Risk:** `drawing_open("../../../etc/passwd")` veya `C:\Windows\System32\...` gibi saldırılar mümkün.

**Çözüm:**
- İzin verilen dizinleri tanımlayan `ALLOWED_PATHS` env değişkeni
- `_validate_path()` yardımcı fonksiyonu ile `Path.resolve()` + `is_relative_to()` kontrolü
- Yazma ve okuma işlemleri için ayrı izin seviyeleri

### 1.2 Komut Enjeksiyonu

**Sorun:** `system_run_command` ve `system_run_lisp` ham string alıyor. LLM veya kullanıcıdan gelen input ile tehlikeli komutlar çalıştırılabilir.

**Çözüm:**
- Whitelist tabanlı komut filtresi
- Tehlikeli pattern tespiti (DELETE, ERASE ALL, PURGE vb.)
- Opsiyonel onay mekanizması (user elicitation)

### 1.3 HTTP Transport Güvenliği

**Sorun:** `fastmcp run --transport http` modunda kimlik doğrulama yok.

**Çözüm:**
- FastMCP `AuthMiddleware` ile OAuth 2.1 entegrasyonu
- API key tabanlı basit auth alternatifi
- Rate limiting middleware

---

## 2. KOD KALİTESİ

### 2.1 Sessiz Hata Yutma

**Sorun:** Birden fazla yerde `except Exception: pass` kullanımı var.

| Konum | Sorun |
|-------|-------|
| `ezdxf_backend.py:108-109` | `_entity_info_dxf` içinde hata yutuluyor |
| `ezdxf_backend.py:818-820` | `block_create_from_entities` içinde sessiz except |
| `server.py:60` | `_detect_autocad_running` hata loglamıyor |

**Çözüm:** Her `except` bloğunda en azından `log.debug()` ile loglama. Kritik yerlerde hata toplama ve raporlama.

### 2.2 Lint & Format Konfigürasyonu

**Sorun:** ruff, flake8, mypy, black, isort gibi araçlar tanımlı değil.

**Çözüm:**
```toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM"]

[tool.ruff.format]
quote-style = "double"

[tool.mypy]
python_version = "3.11"
strict = true
```

### 2.3 Pre-commit Hook

**Çözüm:** `.pre-commit-config.yaml` ile:
- ruff lint + format
- mypy type check
- pytest --quick

---

## 3. TEST ALTYAPISI

### 3.1 Mevcut Kapsam (Düşük)

Sadece ezdxf backend test ediliyor, 17 test var. Test edilmeyen alanlar:

- **server.py** — MCP sunucusu, middleware'ler, tool kayıtları
- **com_backend.py** — COM backend (mock ile test edilebilir)
- **Drawing işlemleri** — `drawing_new`, `drawing_open`, `drawing_save`, export'lar
- **Entity oluşturma** — circle, arc, polyline, text, mtext, hatch, spline, ellipse, point, block_ref
- **Dimension** — linear, aligned, angular, radius, diameter
- **Entity düzenleme** — copy, offset, array_rectangular, set_properties, delete_many
- **Layer işlemleri** — delete, set_current, modify, freeze, thaw, lock, unlock, hide, show
- **Block** — insert, explode, get/set_attributes
- **Analysis** — stats, entities_in_region, measure_distance, measure_area, bounding_box
- **View / System** — tüm tool'lar

### 3.2 Coverage Aracı

**Çözüm:** `pytest-cov` eklenmesi:
```toml
[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
]
```

### 3.3 Test Stratejisi

| Hedef | Yaklaşım |
|-------|----------|
| ezdxf backend | Birim testleri (mevcut + genişletme) |
| COM backend | Mock tabanlı testler (pywin32 mock) |
| server.py | FastMCP test client ile entegrasyon testleri |
| Middleware | İzole birim testleri |

### 3.4 Hedef Coverage

- Kısa vade: %60+
- Orta vade: %80+
- Uzun vade: %90+

---

## 4. CI/CD PİPELINE

### 4.1 GitHub Actions

**Çözüm:** `.github/workflows/ci.yml`:
- Python 3.11, 3.12 matrix
- `pip install -e ".[full]"` + dev dependencies
- `ruff check .` + `ruff format --check .`
- `pytest --cov=. --cov-report=xml`
- Coverage badge güncelleme

### 4.2 Release Otomasyonu

- Tag tabanlı PyPI publish
- Changelog otomasyonu
- Docker image build (opsiyonel)

---

## 5. PERFORMANS İYİLEŞTİRMELERİ

### 5.1 Büyük Çizimlerde Entity Listesi

**Sorun:** `entity_list` tüm modelspace'i iterate ediyor, filtre sonradan uygulanıyor.

**Çözüm:**
- Backend tarafında filtreleme (COM SelectionSet kullanımı)
- Streaming / generator tabanlı entity erişimi
- Sayfalama (pagination) desteği

### 5.2 Analysis İşlemleri

**Sorun:** `analysis_layer_stats` 50.000 limitle tüm entity'leri çekiyor. `analysis_entities_in_region` her entity için bbox hesaplıyor.

**Çözüm:**
- Batch işleme ve streaming
- Spatial index (R-tree) kullanımı
- Sonuç cache'leme (değişiklik yoksa)

### 5.3 Undo Stack Bellek Kullanımı

**Sorun:** ezdxf backend'de tam DXF snapshot'ları `_undo_stack`'te saklanıyor.

**Çözüm:**
- Delta tabanlı undo (sadece değişiklikleri kaydetme)
- Maksimum undo sayısı sınırı
- Snapshot sıkıştırma

### 5.4 Tool Pagination

**Sorun:** 67 araç tek listede sunuluyor.

**Çözüm:** FastMCP `list_page_size` parametresi ile pagination:
```python
mcp = FastMCP("AutoCAD MCP Pro", list_page_size=20)
```

---

## 6. YENİ ÖZELLİK FİKİRLERİ

### 6.1 DWG Doğrudan Desteği

**Mevcut:** ezdxf yalnızca DXF okuyabiliyor.

**Fikir:** ODA File Converter veya LibreDWG ile DWG → DXF otomatik dönüşüm pipeline'ı.

### 6.2 Batch İşlem Desteği

**Fikir:** Tek bir çağrıda birden fazla entity oluşturma/düzenleme:
```python
@mcp.tool()
async def entity_batch_create(entities: list[dict], ctx: Context) -> list[EntityInfo]:
    """Tek çağrıda birden fazla entity oluştur"""
```

### 6.3 Template Sistemi

**Fikir:** Hazır çizim şablonları:
- Başlık bloğu (title block)
- Ölçek barı
- Kuzey oku
- Standart katman setleri (mimari, mekanik, elektrik)

### 6.4 Stil Yönetimi

**Fikir:** Text style, dimension style, linetype yönetimi tool'ları:
```
style_text_create, style_text_list
style_dimension_create, style_dimension_list
linetype_load, linetype_list
```

### 6.5 Koordinat Sistemi Desteği

**Fikir:** UCS (User Coordinate System) yönetimi:
```
ucs_set, ucs_get, ucs_reset, ucs_rotate
```

### 6.6 Annotation Araçları

**Fikir:** Leader, multileader, revision cloud, wipeout:
```
entity_create_leader, entity_create_multileader
entity_create_revision_cloud, entity_create_wipeout
```

### 6.7 Xref Yönetimi

**Fikir:** Harici referans dosyaları:
```
xref_attach, xref_detach, xref_reload, xref_list, xref_bind
```

### 6.8 Layout & Viewport

**Fikir:** Paper space ve viewport yönetimi:
```
layout_create, layout_list, layout_delete
viewport_create, viewport_set_scale, viewport_freeze_layer
```

### 6.9 Table & Schedule

**Fikir:** Tablo oluşturma ve veri çıkarma:
```
table_create, table_set_data, table_extract_data
schedule_create_from_blocks
```

### 6.10 Export Genişletme

**Fikir:** Ek export formatları:
- SVG export (web görüntüleme)
- PNG/JPEG export (ezdxf matplotlib backend)
- STEP/IGES export (3D modeller için)
- JSON export (veri analizi)

---

## 7. KULLANICI DENEYİMİ

### 7.1 Progress Bildirimi

**Fikir:** Uzun süren işlemlerde `ctx.report_progress()` kullanımı:
```python
for i, entity in enumerate(entities):
    await ctx.report_progress(i, total)
```

### 7.2 Daha İyi Hata Mesajları

**Fikir:** Hata mesajlarında çözüm önerisi:
```
"Layer 'WALLS' bulunamadı. Mevcut katmanlar: 0, DOORS, WINDOWS. 
 layer_create('WALLS') ile oluşturabilirsiniz."
```

### 7.3 Akıllı Varsayılanlar

**Fikir:** Entity oluştururken akıllı varsayılanlar:
- Mevcut katmanı otomatik kullan
- Son kullanılan renk/linetype'ı hatırla
- Standart ölçü stilleri otomatik yükle

### 7.4 Çizim Doğrulama

**Fikir:** Çizim kalite kontrol tool'u:
```
validation_check_overlaps       — Üst üste binen entity'ler
validation_check_gaps           — Bağlanmamış çizgiler
validation_check_standards      — Katman/stil standartlarına uyum
validation_check_scale          — Ölçek tutarlılığı
```

---

## 8. DÖKÜMANTASYON

### 8.1 README.md

**Durum:** Eksik (pyproject.toml referans veriyor ama dosya yok).

**İçerik:**
- Proje açıklaması ve özellikler
- Kurulum adımları
- Kullanım örnekleri
- Backend seçimi rehberi
- Tool listesi ve açıklamaları
- Katkıda bulunma rehberi

### 8.2 API Dokümantasyonu

**Fikir:** Her tool grubu için detaylı dokümantasyon:
- Parametre açıklamaları
- Örnek kullanımlar
- Hata senaryoları
- İlişkili tool'lar

### 8.3 Örnek Projeler

**Fikir:** `examples/` dizini altında:
- `01_basic_drawing.py` — Temel çizim oluşturma
- `02_floor_plan.py` — Kat planı oluşturma
- `03_batch_operations.py` — Toplu işlemler
- `04_analysis.py` — Çizim analizi
- `05_export.py` — Farklı formatlara export

### 8.4 .env.example

```env
AUTOCAD_MCP_BACKEND=auto
# ALLOWED_PATHS=/path/to/drawings
# LOG_LEVEL=INFO
```

---

## 9. ALTYAPI

### 9.1 Docker Desteği

**Fikir:** ezdxf backend için Dockerfile:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["python", "server.py"]
```

### 9.2 OpenTelemetry

**Fikir:** Tracing ve metrics:
- Tool çağrı süreleri
- Hata oranları
- Backend durumu
- Entity sayısı metrikleri

### 9.3 Logging İyileştirme

**Fikir:** Structured logging (JSON format):
```python
import structlog
log = structlog.get_logger()
```

### 9.4 Konfigürasyon Yönetimi

**Fikir:** pydantic-settings ile merkezi konfigürasyon:
```python
class Settings(BaseSettings):
    backend: str = "auto"
    allowed_paths: list[str] = []
    max_undo_stack: int = 50
    log_level: str = "INFO"
```

---

## 10. ÖNCELİK MATRİSİ

| # | Fikir | Öncelik | Etki | Zorluk |
|---|-------|---------|------|--------|
| 1 | Path traversal koruması | 🔴 Kritik | Yüksek | Düşük |
| 2 | Komut enjeksiyonu koruması | 🔴 Kritik | Yüksek | Orta |
| 3 | README.md oluşturma | 🟠 Yüksek | Orta | Düşük |
| 4 | Sessiz except düzeltme | 🟠 Yüksek | Orta | Düşük |
| 5 | Ruff lint konfigürasyonu | 🟠 Yüksek | Orta | Düşük |
| 6 | Test kapsamı genişletme | 🟠 Yüksek | Yüksek | Orta |
| 7 | CI/CD pipeline | 🟠 Yüksek | Yüksek | Orta |
| 8 | Batch işlem desteği | 🟡 Orta | Yüksek | Orta |
| 9 | Template sistemi | 🟡 Orta | Yüksek | Orta |
| 10 | Stil yönetimi tool'ları | 🟡 Orta | Orta | Düşük |
| 11 | Annotation araçları | 🟡 Orta | Orta | Orta |
| 12 | Layout & viewport | 🟡 Orta | Yüksek | Yüksek |
| 13 | Performans iyileştirmeleri | 🟡 Orta | Orta | Orta |
| 14 | Progress bildirimi | 🟡 Orta | Orta | Düşük |
| 15 | Çizim doğrulama | 🟢 Düşük | Orta | Orta |
| 16 | Docker desteği | 🟢 Düşük | Düşük | Düşük |
| 17 | OpenTelemetry | 🟢 Düşük | Düşük | Orta |
| 18 | DWG doğrudan desteği | 🟢 Düşük | Yüksek | Yüksek |
| 19 | Xref yönetimi | 🟢 Düşük | Orta | Yüksek |
| 20 | SVG/JSON export | 🟢 Düşük | Orta | Orta |

---

## Sonuç

AutoCAD MCP Pro, güçlü bir temele sahip. 67 tool ile zengin işlevsellik sunuyor ve dual-backend mimarisi esneklik sağlıyor. Öncelikli iyileştirme alanları:

1. **Güvenlik** — Path ve komut koruması production için zorunlu
2. **Kalite** — Lint, test, CI/CD ile sürdürülebilirlik
3. **Yeni özellikler** — Batch, template, stil, annotation ile profesyonel CAD iş akışları
4. **Altyapı** — Docker, telemetry, structured logging ile operasyonel olgunluk
