# AutoCAD MCP Pro — Oturum Notları

Tarih: 2026-06-18  
Kullanıcı: Umutcan Edizsalan (umutcon12@gmail.com)  
Hedef: Projeye tam hakim ol → bug/sorun tespit et → geliştirme yol haritası üret → onay sonrası uygula.

---

## YAPILDI ✅ — RECON Workflow (Task #1)

### Ne yapıldı
- 16 subagent çalıştırıldı: 8 kod-haritalama + 7 web araştırması + 1 sentez.
- Tüm kod tabanı `file:line` hassasiyetinde haritalandı.
- Web araştırması (arXiv, rakip MCP'ler, ezdxf/COM API, ISO standartları) tamamlandı.
- Sentez dosyası: `docs/analysis/00-RECON-dossier.md` (31KB, tam rapor)
- Ham veri: `docs/analysis/_recon_raw.json`

### Temel Bulgular

**Gerçek sayılar (dökümanda ne yazıyor vs gerçek):**
| Konu | Dökümanda | Gerçek |
|---|---|---|
| Tool sayısı | "87 tools" | **109 @mcp.tool** |
| Test sayısı | "104 tests" | **184 test fonksiyonu** |
| Section 1 | "(11 tools)" | **12 araç** (drawing_redo fazla) |
| Section 9 | "(5 tools)" | **4 araç** |
| LICENSE dosyası | "MIT — see LICENSE" | **YOK** (legal açık) |
| CI (.github/workflows/ci.yml) | "GitHub Actions CI" | **SİLİNMİŞ** |
| benchmarks/ klasörü | referans var | **YOK** |
| .claude/skills/ ve .cursor/ | referans var | **GIT'TEN SİLİNMİŞ** |

---

## YAPILDI ✅ — FAZ 1: P0 FIX (commit cd6329a, branch fix/p0-com-premium-lineweight)

- **R1 FİXLENDİ:** 8 premium meta-tool base sınıfına (AutoCADBackend) concrete + backend-agnostik olarak taşındı → COM artık miras alıyor, çökme bitti. Tek backend-özel parça yeni `_create_xline` primitifi. ezdxf'ten ~285 satır tekrar silindi.
- **R2 FİXLENDİ:** `normalize_lineweight()` eklendi (mm-float ↔ hundredths-int konvansiyon çakışması çözüldü); 6 çağrı sitesine bağlandı. ISO-128 lineweight'ler artık 0'a yuvarlanmıyor.
- **R3 FİXLENDİ:** iso128 kritiği artık ateşleniyor (R2 sayesinde); CONSTRUCTION katmanları muaf tutuldu (yanlış-pozitif engeli); yanıltıcı yorum düzeltildi.
- **LICENSE** eklendi (MIT). **ci.yml** geri yüklendi (lint geçici non-blocking; test job gerçek gate).
- **Doğrulama:** 182 passed / 2 xfailed + fonksiyonel test (GEOMETRY lw=50, kritik 0.40mm'yi yakalıyor).

---

## YAPILDI ✅ — FAZ 2: DIAGNOSTICS + IDEAS (workflow'lar)

- **DIAGNOSTICS** (`docs/analysis/01-DIAGNOSTICS.md`): 31 doğrulandı, 28 onaylandı, 3 reddedildi (R25/R29/R17 adversarial olarak çürütüldü), taramadan 17 yeni bulgu. → 0 CRITICAL (R1-R3 fixli), 2 HIGH (N1 COM hatch, N2 save-format), 14 MED, 10 LOW, 14 SMELL.
- **IDEAS/ROADMAP** (`docs/analysis/02-ROADMAP.md`): 19 fikir Impact×Effort×Diff×Evidence ile skorlandı, 9'u challenge edildi. Sprint 1 (correctness+quick wins) → Phase A (closed-loop moat) → Phase B (ISO production) → Phase C (breadth).
- **İki kritik yeni bulgu:** (1) HTTP auth hiç zorlanmıyor (latent güvenlik), (2) `drawing_finalize` `run_critique`'i HİÇ çağırmıyor — moat finalize'da devrede değil.
- **R7/R8 güvenlik:** otomatik doğrulanamadı (cyber-filter) → savunmacı hardening kalemi olarak Sprint 1'e eklendi.

**Önerilen sonraki 5:** ① I16 correctness bundle + I19 COM test harness · ② I9 deterministik geometri · ③ I12 HTTP auth + I2 render-as-image · ④ I4 scalar score + I15 birleşik validator · ⑤ I6 GD&T.

**Durum: Task #4 (konsolide rapor) HAZIR → kullanıcı onayı bekleniyor (FAZ 3 = uygulama).**

---

## KRİTİK BUGLAR (R1-R3 ARTIK FİXLİ — kalanlar FAZ 2 DIAGNOSTICS'te doğrulandı)

### R1 — KRİTİK: Premium araçlar COM'da çöküyor
- **Konum:** `backends/com_backend.py:1637-1660`
- **Sorun:** 8 premium meta-tool (`drawing_plan`, `drawing_critique`, `point_from_snap`, `construction_xline`, `construction_clear`, `drawing_apply_iso_layers`, `dimension_auto`, `entity_select_smart`) COM backend'inde `NotImplementedError` fırlatıyor.
- **Sonuç:** CLAUDE.md'nin "üretim için olmazsa olmaz" dediği akış, **Windows'taki varsayılan backend'de (COM) çöküyor**. Yani kullanıcı AutoCAD açıp kullandığında bu araçlar çalışmıyor.

### R2 — KRİTİK: Lineweight sıfırlanıyor
- **Konum:** `backends/ezdxf_backend.py:1034`
- **Sorun:** `int(lineweight)` → 0.50, 0.25, 0.18, 0.13 mm gibi tüm ISO-128 değerleri **0'a yuvarlanıyor**.
- **Sonuç:** Tüm ISO-128 çizgi kalınlığı disiplini sessizce sıfırlanıyor. `drawing_apply_iso_layers` ve `drawing_new` bootstrap'ı da etkileniyor.

### R3 — YÜKSEK: ISO-128 kritiği kalıcı no-op
- **Konum:** `engineering/critique.py:50`
- **Sorun:** `_check_iso128` içinde `lw <= 0: continue` → R2 yüzünden zaten hepsi 0 → kritik hiçbir zaman ateşlenmiyor.

---

## RİSK KAYITÇISI (Tüm Bulgular, Öncelik Sırasına Göre)

### KRİTİK (2 adet)
| # | Konu | Konum |
|---|---|---|
| R1 | 8 premium araç COM'da NotImplementedError | com_backend.py:1637-1660 |
| R2 | int(lineweight) → 0, tüm ISO-128 sıfırlandı | ezdxf_backend.py:1034 |

### YÜKSEK (8 adet)
| # | Konu | Konum |
|---|---|---|
| R3 | iso128 kritiği kalıcı no-op | critique.py:50 |
| R4 | dim_overlap kritiği da no-op (properties yok) | critique.py:194-197 |
| R5 | COM timeout → thread leak + CoUninitialize yok | com_backend.py:415-433 |
| R6 | COM backend'de SIFIR test | tests/ (ComBackend import yok) |
| R7 | Server→sanitizer wiring testsiz | server.py:2035,2052 |
| R8 | LISP aliasing bypass testi yok | security.py:138-179 |

### ORTA (21 adet)
| # | Konu | Konum |
|---|---|---|
| R9 | entity_array_polar 360° → son kopya 0°=orijinal çakışır | ezdxf_backend.py:946-947 |
| R10 | drawing_finalize fmt belirtmiyor → 3 farklı davranış | server.py:2299 |
| R11 | drawing_save_as(fmt='dwg') ezdxf'de DXF bayt yazar, .dwg ismiyle | ezdxf_backend.py:345-352 |
| R12 | dimension_angular tx/ty yok sayıyor, fixed distance=10 | ezdxf_backend.py:705-722 |
| R13 | entity_offset side_x/side_y her iki backend'de de yok sayılıyor | ezdxf:868-908 / com:860-874 |
| R14 | engineering import guard → None → opaque "NoneType not callable" | server.py:2266,2294 |
| R15 | system_about tool_groups → 15 tool eksik, drifted | server.py:2070-2106 |
| R16 | COM transaction_active sızıntısı hata durumunda | com_backend.py:1402 |
| R17 | _safe_send_command busy-poll STA thread'i bloke ediyor | com_backend.py:1521-1536 |
| R18 | drawing_new bootstrap hatalarını yutuyor, başarı döndürüyor | server.py:280-294 |
| R19 | dimension_aligned/angular kalıcı xfail, kırık araçlar gönderildi | tests/test_dimensions.py:16-27 |
| ... | (+ 10 daha orta öncelikli risk) | |

### DÜŞÜK (22 adet)
| # | Konu | Konum |
|---|---|---|
| R20 | _registered_tool_count FastMCP iç yapısına bağımlı | server.py:231-234 |
| R21 | Involute dişi geometrisi matematiksel hatalı (trochoid fillet yok) | engineering/gear.py:40-50 |
| R22 | undo/transaction stack paylaşıyor, doc_path sıfırlanmıyor | ezdxf_backend.py:470-484 |
| R23 | COM run_lisp her zaman 'nil' döndürüyor | com_backend.py:1487-1492 |
| R24 | _apply_attrs linetype'ı yüklemeden set ediyor | ezdxf_backend.py:491-501 |
| R25 | block_find_references max_list_limit bypass | server.py:1362-1370 |
| R26 | view zoom ezdxf'de no-op ama success döndürüyor | server.py:1814-1831 |
| R27 | validator title check false-positive ('SPUR' içeren notta) | engineering/validator.py:166-181 |
| R28 | COM HWND palette/splash dialog'u yakalayabilir | com_backend.py:283-300 |
| R29 | ~20 sitede except Exception: pass COM hatalarını yutuyor | com_backend.py:199,244,… |

### KOD KOKUSU / ANLAMSIZ KOD (53 adet)
- `engineering/section.py` — tamamen dead code, sıfır caller, sıfır test
- `gear.generate_tooth_profile` — dead code (export edilmiş ama hiç çağrılmıyor)
- `BlockInfo.description` field — hiç doldurulmuyor (her iki backend'de)
- `critique.py:53` "normalises to mm" yorumu — FALSE COMMENT
- `engineering/__init__.py:37-39` "Agent B … in flight" / "Task #7/#8" — çok-agent build seam üretime gönderilmiş
- `_LAYER_TEMPLATES` (server.py) ve prompt layer set'leri çakışıyor/kopyalanmış
- `template_list` / `validation_check` saf in-memory, yeterli test yok
- `system_about` static catalog 15 araç eksik
- ... (+ 40 daha smell)

---

## TEST KAPSAMASI (Eksikler)

1. **COM backend: %0 coverage** — en riskli yer, sıfır test
2. **Server→sanitizer entegrasyon** — araçlar sanitizer'ı gerçekten çağırıyor mu? Test yok
3. **LISP adversarial bypass** — aliasing, UNC path vs test yok
4. **Critique detection paths** — sadece temiz çizimde test edilmiş (hata bulmuyor mu diye değil)
5. `dimension_auto ordinate` — testsiz
6. `dimension_aligned/angular` — kalıcı xfail (kırık gönderilmiş)
7. Pek çok backend metodu hiç test edilmemiyor (system_get/set_variable, drawing_close, view_screenshot, ...)

---

## ARAŞTIRMA ÖZETİ (Ne bulduk)

### Akademik (arXiv 2025-2026)
- **GeoGramBench (ICLR 2026):** LLM'ler koordinat hesaplamada <%50 başarı → `point_from_snap` yaklaşımımızı doğruluyor, genişletmek lazım
- **CADSmith:** 5-agent döngüsü (Planner/Coder/Executor/Validator/Refiner) + VLM render → Chamfer 38× iyileştirme. **Render → VLM judge döngüsü en yüksek kaldıraç**
- **Self-Improving CAD + FEA:** İterasyon per token'dan çok daha değerli; drawing_critique tek seferlik değil döngü olmalı
- **ProCAD:** Çizmeden önce belirsizlik tespiti → hata oranı %14.6 → %0.9

### Rakip MCP'ler
| Rakip | 3D | Render-Critique | Validation Gate |
|---|---|---|---|
| **Bizim (AutoCAD MCP Pro)** | ❌ | ⚠️ finalize-only | ✅ **UNIQUE** |
| build123d-mcp | ✅ | ✅ | ❌ |
| FreeCAD MCP (150+ tool) | ✅ + FEM | ⚠️ | ❌ |
| Blender MCP (22k★) | ✅ | ✅ | ❌ |
| RhinoMCP | ✅ | ✅ | ❌ |

**Moatımız: Standards-validation gate — kimse yapmıyor.**  
**Gerideyiz: 3D, in-loop render-critique, HTTP auth.**

---

## KALAN GÖREVLER ⏳

### Task #2 — DIAGNOSTICS Workflow
- Bug'ları `file:line` doğruluğuyla teyit et
- Ölü kodu + anlamsız kodlamaları listele
- Çekişmeli doğrulama (refute) sonrası "onaylanmış bulgu listesi" üret
- **Durum: Bekliyor (RECON tamamlandı, hazır)**

### Task #3 — IDEAS Workflow
- RECON araştırmasından türetilen fikir adayları oluştur
- Impact × Effort × Differentiation skoru
- Önceliklendirilmiş, kanıta dayalı yol haritası
- **Durum: DIAGNOSTICS bitmesini bekliyor**

### Task #4 — Konsolide Rapor + Onay
- RECON + DIAGNOSTICS + IDEAS birleştir
- Kullanıcıya sun
- **Onay sonrası** kodlamaya geç (kullanıcı bu tercihi seçti)

---

## DOSYALAR

| Dosya | İçerik |
|---|---|
| `docs/analysis/00-RECON-dossier.md` | Tam sentez raporu (31KB) |
| `docs/analysis/_recon_raw.json` | Ham yapılandırılmış veri |
| `not.md` | Bu dosya — oturum notları |

---

## ÖNERİLEN FIX ÖNCELİKLERİ (Onay Bekleniyor)

**P0 — Hemen Çalışmaz Olanlar (Onay Sonrası Fix)**
1. R1: `com_backend.py:1637-1660` → 8 premium aracı COM'a port et
2. R2: `ezdxf_backend.py:1034` → `int(lineweight * 100)` veya enum map ile düzelt
3. LICENSE dosyası ekle (legal açık)
4. CI (ci.yml) geri yükle veya yeniden kur

**P1 — Kritik Kalite (Onay Sonrası)**
5. `drawing_critique` → iteratif refiner döngüsü
6. Finalize screenshot'ı VLM judge'a besle
7. `drawing_plan`'a pre-flight ambiguity detector ekle
8. COM testleri: mock veya live fixture

**P2 — Üretim Çizim Kalitesi**
9. ISO-129 toleranslar + GD&T çerçevesi
10. PaperSpace/Layout/Plot desteği (COM)
11. odafc ile gerçek DWG export (ezdxf)

**P3 — Kapsam Genişletme**
12. 3D solid tier (COM extrude/revolve/boolean)
13. Parametrik yeniden sürüş (driving dims → re-drive tool)
14. HTTP API-key auth middleware
