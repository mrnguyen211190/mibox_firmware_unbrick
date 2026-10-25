# Cứu Xiaomi Mi Box MDZ-16-AB: nhật ký và ghi chú (2026-10-25)

## TL;DR

- **Thiết bị:** Xiaomi Mi Box 3 bản quốc tế, **MDZ-16-AB** (tên mã `once`), chip Amlogic S905X (GXL), RAM 2 GB, eMMC 8 GB. Không có cổng LAN.
- **Triệu chứng:** cắm điện + HDMI thì màn hình đen. Cắm USB A-A vào PC thì hiện ra **GX-CHIP / WorldCup Device** (`VID_1B8E&PID_C003`).
- **Kết quả:** **CHƯA CỨU ĐƯỢC.** Đã đưa được box lên chế độ nạp của u-boot, nhưng u-boot **không đọc/ghi được eMMC** (`disk_initial`, `store init`, `mmc ...` đều `failed`). **Nhiều khả năng eMMC hỏng phần cứng.** Box chưa bị ghi gì vào bộ nhớ trong.
- **Hướng tiếp theo:** mang ra tiệm có máy nạp eMMC để kiểm tra hoặc thay chip, rồi ghi `mdz16ab.img`. Nhớ mang theo `password.bin`. Hoặc bỏ, mua thiết bị khác làm server mini.

---

## Các file trong thư mục

| File / thư mục | Là gì |
|---|---|
| `mdz16ab.img` | Image USB Burning Tool cho MDZ-16-AB, Android 8.0 build 2167 (1,6 GB). Do cộng đồng chia sẻ, nguồn: [Fengmi 4K Memo](https://sites.google.com/view/fengmi-4k-memo/mibox/download). Đã kiểm tra CRC của image: OK. **Thiếu mục USB DDR/UBOOT** nên tool không nạp được box đang ở chế độ ROM (xem phần 3). |
| `Xiaomi_Mi_Box_MDZ-16-AB_8.0_OTA.zip` | OTA chính thức build 2179, tải từ server Google (`android.googleapis.com/packages/ota-api/xiaomi_once_once/5c7bf1ed...zip`). Chỉ cài được qua recovery, khi box đã chạy lại Android. |
| `password.bin` | **Mật khẩu mở khóa chế độ nạp USB** (16 byte ASCII). Đã xác nhận đúng với box này: gửi xong thì `Password OK` chuyển từ 0 sang 1. Nguồn: AndroidPCTV (link Mega). |
| `xiaomi_mi_box_password_bin.zip` | File zip gốc chứa `password.bin` (kèm readme và 2 shortcut web). |
| `MDZ-16-AB_diem_chap_*.jpg/png` | Ảnh vị trí 2 chấm đồng để chập eMMC. **Thực tế không cần dùng**, vì box đã tự ở chế độ ROM. |
| `tools/` | USB Burning Tool (bản cài thực tế báo V2.1.9.0) và mã nguồn pyamlboot (`pyamlboot-master.zip`). |
| `scripts/` | Các script Python đã dùng (xem phần 5). |
| `scripts/thu_nghiem_that_bai/` | Các script thử nghiệm không thành công, giữ lại để tham khảo. |
| `logs/` | Log USB Burning Tool, log pyamlboot, kết quả chẩn đoán eMMC, `burn_config.xml` mà tool sinh ra từ image. |

---

## Nhật ký theo thứ tự

### 1. Xác định tình trạng
- Máy tính nhận box là `GX-CHIP`, ban đầu báo lỗi driver. Sau khi cài USB Burning Tool thì thành `WorldCup Device` (libusb-win32 1.2.6.0).
- Rút USB, chỉ cắm adapter + HDMI: vẫn đen màn hình. Kết luận: bootloader trong eMMC không chạy được.

### 2. USB Burning Tool kẹt ở `low_power` 1%
- Log báo `[0x30101004] UBOOT/Low power/Send command/Error result`. Tool gửi `low_power` 10 lần, box không trả lời.
- Đã thử: cắm thêm adapter nguồn, chập 2 chấm đồng eMMC, đổi thứ tự cắm. **Không có tác dụng.**
- Ô "Erase bootloader" trong UI không bỏ chọn được, vì `BurnCfgUI.ini` luôn ghi `EraseBootLoader Enable = 1`. Dòng `ERASE BOOTLOADER` trong log chỉ là tên giai đoạn, không phải nguyên nhân gây kẹt.

### 3. Tìm ra nguyên nhân thật
Đọc trạng thái box bằng lệnh identify (`scripts/ident.py`, chỉ đọc, không ghi gì):

```
2-2-0-0-1-0-0-0
│ │ │ │ │ └ Password OK = 0
│ │ │ │ └── Need Password = 1   -> chế độ nạp bị khóa mật khẩu
│ │ └─┴──── Stage 0.0 = IPL     -> chip đang ở chế độ ROM (bootloader trong eMMC không chạy)
└─┴──────── ROM version 2.2
```
Ý nghĩa các byte theo `socid.py` / `PROTOCOL.md` của pyamlboot. Các giai đoạn: `0.0` = IPL (ROM), `0.8` = SPL (BL2), `0.16` = TPL (u-boot, chế độ nạp).

Có 2 vấn đề chồng lên nhau:
1. **Chế độ nạp bị Xiaomi khóa bằng mật khẩu.** USB Burning Tool không gửi mật khẩu, kể cả khi đã đặt đường dẫn trong `PassWordPath.ini`.
2. **`mdz16ab.img` không có mục `USB/DDR(_ENC)` và `USB/UBOOT(_ENC)`.** Trình tự nạp mà tool sinh ra (`logs/burn_config_tu_mdz16ab_img.xml`) **bắt đầu luôn bằng `low_power`**, tức là giả định box đã chạy u-boot. Với box đang ở ROM thì không bao giờ chạy được. Một người trên XDA báo đúng hiện tượng này với 6 box: "all 6 go to maskrom, all 6 stop in 1%-low_power".

### 4. Đưa box từ ROM lên u-boot (chỉ ghi vào RAM): THÀNH CÔNG
1. `scripts/sendpwd.py`: gửi `password.bin` bằng `REQ_PASSWORD` (0x35), ra `Password OK = 1`.
   - Lưu ý: hàm `sendPassword` của pyamlboot có `sleep(2)` trước khi kiểm tra, và box **không nhận** theo cách đó. Phải dùng script riêng, identify ngay sau khi gửi.
   - Mật khẩu mất mỗi khi box khởi động lại, phải gửi lại.
2. `scripts/to_tpl.py`: chạy các bước `optimus` của pyamlboot (SecureBoot check, Download SPL, Download UBOOT). Các mục USB được **tự tạo từ phân vùng `bootloader`** của image:
   - `DDR_ENC` = 0xC000 (49152) byte đầu của bootloader
   - `UBOOT_ENC` = phần còn lại (852480 byte)
   - Secure boot đang bật (`Encrypt_reg 0xc8100228 = 0xbdfd71be`, bit 0x10).
   - Tham số BL2 cho GXL: `0xc0df` (khởi tạo DDR), `0xc0e0` (load addr + **size + checksum** của TPL), `0xc0e1` (chạy).
   - Kết quả: box lên **`0-7-0-16` (TPL)**, chế độ nạp của u-boot.
3. Bài học từ các lần thất bại trước đó (`scripts/thu_nghiem_that_bai/`): file `usbbl2runpara_runfipimg.bin` dùng chung của pyamlboot có size cố định 0xa4000, không khớp với TPL 852480 byte nên BL2 khởi động lại box. Ngoài ra, ở giai đoạn ROM, ghi bulk khối nhỏ (32/64 byte) bị timeout, phải ghi bằng control transfer hoặc khối 4 KB.

### 5. Ghi firmware: THẤT BẠI tại `disk_initial`
- `scripts/flash.py`: chạy toàn bộ quy trình `optimus` của pyamlboot, có thêm các mục USB tự tạo. Thứ tự đã sửa: nạp `dtb meson1` vào RAM **trước** `disk_initial`, giống `burn_config.xml`. Tùy chọn: không xóa bootloader, normal wipe.
- Đến `low_power` thì OK, lần đầu tiên box trả lời lệnh này. Nạp `dtb` cũng OK. Nhưng **`disk_initial 1` báo `failed`**. Xem `logs/flash_disk_initial_failed.log`.
- `scripts/diag.py`: gửi thêm các lệnh chỉ đọc (kết quả trong `logs/chan_doan_emmc_2026-10-25.txt`). Mọi lệnh liên quan eMMC đều `failed`, chỉ các lệnh không đụng chip nhớ là `success`.
- **Kết luận:** nhiều khả năng eMMC hỏng. Điều này cũng giải thích vì sao box rơi về chế độ ROM ngay từ đầu. **Chưa xác nhận bằng UART**: u-boot chỉ trả success/failed, không có text lỗi.

---

## Hướng dẫn chạy lại các script

### Chuẩn bị (một lần)
```bash
# Python 3.10+; driver libusb-win32 đã được USB Burning Tool cài sẵn (C:\Windows\System32\libusb0.dll)
python -m pip install --target pylib pyusb pycryptodome
unzip tools/pyamlboot-master.zip          # ra thư mục pyamlboot-master/
```
**Tắt hẳn USB Burning Tool trước khi chạy script.** Nếu tool đang mở, nó giữ cổng USB và script sẽ báo "resource is in use". Cắm cáp USB A-A trước, rồi mới cắm adapter.

### Các script trong `scripts/`
| Script | Chức năng | Ghi vào box? | Cách chạy |
|---|---|---|---|
| `ident.py` | Đọc trạng thái (identify) | Không | `python -I ident.py pylib` |
| `sendpwd.py` | Gửi `password.bin` **1 lần** (chỉ gửi nếu box đang báo khóa) | Không ghi bộ nhớ | `python -I sendpwd.py pylib password.bin` |
| `to_tpl.py` | ROM → u-boot (TPL), chỉ ghi RAM. **Chạy `sendpwd.py` trước.** | Chỉ RAM | `python -I to_tpl.py pylib pyamlboot-master mdz16ab.img password.bin` |
| `diag.py` | Gửi lệnh u-boot (bulkcmd), in success/failed. Box phải ở TPL. | Tùy lệnh, **chỉ dùng lệnh đọc** | `python -I diag.py pylib pyamlboot-master "amlmmc rescan 1" "store init 0"` |
| `flash.py` | Nạp toàn bộ `mdz16ab.img` (no erase bootloader, normal wipe, reset khi xong) | **CÓ, ghi eMMC** | `python -I flash.py pylib pyamlboot-master mdz16ab.img password.bin` |
| `amlimg.py` | Liệt kê các mục trong file `.img` Amlogic và kiểm tra CRC | Không | `python -I amlimg.py mdz16ab.img` |
| `amlx.py` | Trích `platform.conf` và `bootloader.img` từ image | Không | `python -I amlx.py mdz16ab.img <thư_mục_ra>` |

**Trình tự đầy đủ nếu sau này thay eMMC xong mà vẫn muốn tự nạp qua USB:**
`ident.py` (phải ra `...-1-0-...`) → `sendpwd.py` (ra `...-1-1-...`) → `to_tpl.py` (ra `0-7-0-16`) → `flash.py`.

---

## Ghi chú quan trọng
- **Không chọn "Erase all"** và cố **không xóa bootloader**, để giữ khóa DRM (Netflix HD) và địa chỉ MAC.
- Box tắt điện hay khởi động lại thì quay về ROM và bị khóa lại. Phải chạy lại `sendpwd.py` rồi `to_tpl.py`.
- Bỏ remote vẫn điều khiển được box bằng chuột/bàn phím USB, app Google TV trên điện thoại, hoặc ADB/scrcpy.
- Các link đã chết (tại thời điểm 2026-10-25): Mega `ag4U1TxR` (unbrick image trong thread firmware XDA, lỗi -16), Google Drive folder `1-fGnIP7iLmpHUNRPhlWyEnEVHuraDc1q` (404). Link Google Drive gốc của OTA bị "Quota exceeded", đã thay bằng link server Google ở trên.

## Nguồn tham khảo
- pyamlboot (protocol, optimus): https://github.com/superna9999/pyamlboot
- XDA: Mi-box stuck/bricked MDZ-16-AB: https://xdaforums.com/t/help-mi-box-stuck-bricked-mdz-16-ab.3834421/
- XDA: Official Stock Firmware Thread (MDZ-16-AB / MDZ-22-AB): https://xdaforums.com/t/official-stock-firmware-thread-mi-box-mdz-16-ab-and-mdz-22-ab.4241475/
- XDA: Unbrick Mi Box 3 MDZ-16-AA: https://xdaforums.com/t/s905x-unbrick-xiaomi-mi-box-3-mdz-16-aa.3502992/
- AndroidPCTV: Mi Box recover from brick: https://androidpctv.com/?p=19929
- Fengmi 4K Memo (mdz16ab.img, USB Burning Tool): https://sites.google.com/view/fengmi-4k-memo/mibox/download
- CoreELEC: Xiaomi Mi BOX, CE and DRM (Armbian trên MDZ-16-AB): https://discourse.coreelec.org/t/xiaomi-mi-box-ce-and-drm/834

https://mega.nz/file/JF8wABKb#oaaNkKaw_XWZesV0KBPLxHgVUEaryij--9vtBdUoeqY (mdz16ab.img)
https://mega.nz/file/gE0xkIab#smiAvMDeTSfYIVyUk52aAv-kddCw_uMECrCdoJUsB7c (Xiaomi_Mi_Box_MDZ-16-AB_8.0_OTA.zip)