# -*- coding: utf-8 -*-
"""
sign_info.py
Tra cứu TÊN và Ý NGHĨA CHI TIẾT của từng mã biển báo cụ thể
theo QCVN 41:2019/BGTVT (Quy chuẩn kỹ thuật quốc gia về báo hiệu đường bộ).

Cách dùng:
    from src.sign_info import get_sign_info
    info = get_sign_info("P.130")
    # -> {"name": "Cấm dừng xe và đỗ xe", "meaning": "..."}

Nếu class_name chưa có trong SIGN_INFO, get_sign_info() sẽ trả về một mô tả
mặc định dựa theo NHÓM biển (suy ra từ tiền tố mã: P/W/R/S/DP), để giao diện
luôn có nội dung hiển thị thay vì để trống.

LƯU Ý CHO NGƯỜI DÙNG: Dữ liệu bên dưới được biên soạn theo đúng danh mục tên
biển tại Chương 4, 5, 6 và Phụ lục B/C/D/F của QCVN 41:2019/BGTVT. Nếu model
của bạn dùng bộ 58 lớp riêng (đặt tên khác hoặc đánh số khác chuẩn), hãy đối
chiếu với file classes.txt / data.yaml của bạn và bổ sung/sửa lại dict bên
dưới cho khớp chính xác 58 lớp thực tế.
"""

SIGN_INFO = {
    # ------------------------------------------------------------------ #
    # NHÓM P — BIỂN BÁO CẤM (Chương 4, Phụ lục B)
    # ------------------------------------------------------------------ #
    "P.101": {"name": "Đường cấm", "meaning": "Báo đường cấm tất cả các loại phương tiện đi lại cả hai hướng, trừ các xe được ưu tiên theo quy định."},
    "P.102": {"name": "Cấm đi ngược chiều", "meaning": "Báo đường cấm các loại xe (cơ giới và thô sơ) đi vào theo chiều đặt biển, trừ xe ưu tiên. Người đi bộ được phép đi trên vỉa hè hoặc lề đường."},
    "P.103a": {"name": "Cấm xe ô tô", "meaning": "Cấm các loại xe cơ giới, kể cả mô tô ba bánh có thùng, đi vào đoạn đường đặt biển. Mô tô hai bánh, xe gắn máy và các xe được ưu tiên theo luật vẫn được đi."},
    "P.103b": {"name": "Cấm xe ô tô rẽ trái", "meaning": "Cấm các loại xe ô tô rẽ trái (áp dụng cho cả xe ô tô kéo rơ-moóc hoặc sơ-mi rơ-moóc)."},
    "P.103c": {"name": "Cấm xe ô tô rẽ phải", "meaning": "Cấm các loại xe ô tô rẽ phải (áp dụng cho cả xe ô tô kéo rơ-moóc hoặc sơ-mi rơ-moóc)."},
    "P.104": {"name": "Cấm xe máy", "meaning": "Cấm mô tô và xe máy đi vào, trừ trường hợp xe được ưu tiên theo luật. Biển không cấm xe đạp."},
    "P.105": {"name": "Cấm xe ô tô và xe máy", "meaning": "Cấm cả xe ô tô và mô tô, xe máy đi vào đoạn đường, trừ xe được ưu tiên theo quy định."},
    "P.106a": {"name": "Cấm xe ô tô tải", "meaning": "Cấm các loại xe ô tô tải (trừ các xe được ưu tiên) đi vào. Nếu có ghi trọng tải trên biển thì chỉ cấm loại xe tải có trọng lượng lớn hơn giá trị ghi trên biển."},
    "P.106b": {"name": "Cấm xe ô tô tải", "meaning": "Biến thể của biển cấm xe ô tô tải, thường ghi kèm trọng tải cụ thể (ví dụ trên X tấn) để chỉ rõ loại xe tải bị cấm."},
    "P.106c": {"name": "Cấm các xe chở hàng nguy hiểm", "meaning": "Cấm các xe chuyên chở hàng hóa nguy hiểm (dễ cháy nổ, hóa chất độc hại...) đi vào đoạn đường đặt biển."},
    "P.107": {"name": "Cấm xe ô tô khách và xe ô tô tải", "meaning": "Cấm đồng thời cả xe ô tô chở khách và xe ô tô tải đi vào đoạn đường."},
    "P.107a": {"name": "Cấm xe ô tô khách", "meaning": "Cấm các loại xe ô tô chở khách (trên 9 chỗ) đi vào, trừ xe buýt trên tuyến quy định."},
    "P.107b": {"name": "Cấm xe ô tô taxi", "meaning": "Cấm xe taxi đi vào đoạn đường đặt biển, thường dùng ở khu vực hạn chế taxi ra vào."},
    "P.108": {"name": "Cấm xe kéo rơ-moóc", "meaning": "Cấm các loại xe cơ giới đang kéo theo rơ-moóc đi vào đoạn đường."},
    "P.108a": {"name": "Cấm xe sơ-mi rơ-moóc", "meaning": "Cấm xe ô tô đầu kéo đang kéo sơ-mi rơ-moóc đi vào đoạn đường."},
    "P.109": {"name": "Cấm máy kéo", "meaning": "Cấm các loại máy kéo (kể cả máy kéo có kéo theo rơ-moóc) đi vào đoạn đường."},
    "P.110a": {"name": "Cấm xe đạp", "meaning": "Cấm xe đạp đi vào đoạn đường, trừ xe đạp của người khuyết tật."},
    "P.110b": {"name": "Cấm xe đạp thồ", "meaning": "Cấm loại xe đạp chở hàng cồng kềnh (xe đạp thồ) đi vào đoạn đường."},
    "P.111a": {"name": "Cấm xe gắn máy", "meaning": "Cấm xe gắn máy (loại có dung tích xy-lanh nhỏ hoặc động cơ điện, tốc độ thiết kế không quá 50km/h) đi vào."},
    "P.111b": {"name": "Cấm xe ba bánh loại có động cơ", "meaning": "Cấm xe ba bánh có động cơ (xe lam, xích lô máy...) đi vào đoạn đường."},
    "P.111c": {"name": "Cấm xe ba bánh loại có động cơ", "meaning": "Cấm xe ba bánh có động cơ (xe lam, xích lô máy...) đi vào đoạn đường (biển ghép chiều ngược lại)."},
    "P.111d": {"name": "Cấm xe ba bánh loại không có động cơ", "meaning": "Cấm xe ba bánh không có động cơ (xích lô đạp) đi vào đoạn đường."},
    "P.112": {"name": "Cấm người đi bộ", "meaning": "Cấm người đi bộ đi vào đoạn đường đặt biển, thường dùng cho đường cao tốc hoặc đoạn đường nguy hiểm."},
    "P.113": {"name": "Cấm xe người kéo, đẩy", "meaning": "Cấm các loại xe thô sơ do người kéo hoặc đẩy đi vào đoạn đường."},
    "P.114": {"name": "Cấm xe súc vật kéo", "meaning": "Cấm các loại xe do súc vật kéo đi vào đoạn đường."},
    "P.115": {"name": "Hạn chế trọng tải toàn bộ xe cho phép", "meaning": "Cấm các xe (kể cả xe được ưu tiên) có trọng tải toàn bộ (tải trọng bản thân xe + hàng chở) vượt quá trị số ghi trên biển đi vào."},
    "P.116": {"name": "Hạn chế tải trọng trục xe", "meaning": "Cấm các xe có tải trọng phân bổ trên trục xe (trục đơn) vượt quá trị số ghi trên biển đi vào."},
    "P.117": {"name": "Hạn chế chiều cao", "meaning": "Báo hạn chế chiều cao cho phép của xe (kể cả hàng hóa xếp trên xe nếu có) khi đi qua đoạn đường, cầu, cống, hầm... Trị số ghi trên biển là chiều cao tối đa cho phép, tính bằng mét."},
    "P.118": {"name": "Hạn chế chiều ngang xe", "meaning": "Báo hạn chế bề rộng của xe (kể cả hàng hóa xếp trên xe) được phép đi qua đoạn đường."},
    "P.119": {"name": "Hạn chế chiều dài xe", "meaning": "Báo hạn chế chiều dài của xe (kể cả hàng hóa) được phép đi qua đoạn đường."},
    "P.120": {"name": "Hạn chế chiều dài xe cơ giới kéo theo rơ-moóc hoặc sơ-mi rơ-moóc", "meaning": "Báo hạn chế chiều dài của tổ hợp xe cơ giới đang kéo rơ-moóc hoặc sơ-mi rơ-moóc khi đi qua đoạn đường."},
    "P.121": {"name": "Cự ly tối thiểu giữa hai xe", "meaning": "Báo cho lái xe phải giữ khoảng cách tối thiểu (m) với xe phía trước, thường đặt tại đoạn đường đèo dốc, tầm nhìn hạn chế."},
    "P.123a": {"name": "Cấm rẽ trái", "meaning": "Cấm các loại xe rẽ trái tại vị trí đặt biển (trừ trường hợp có biển phụ cho phép một số loại xe)."},
    "P.123b": {"name": "Cấm rẽ phải", "meaning": "Cấm các loại xe rẽ phải tại vị trí đặt biển (trừ trường hợp có biển phụ cho phép một số loại xe)."},
    "P.124a": {"name": "Cấm quay đầu xe", "meaning": "Cấm tất cả các loại xe quay đầu (theo kiểu chữ U) tại vị trí đặt biển."},
    "P.124b": {"name": "Cấm ô tô quay đầu xe", "meaning": "Cấm riêng xe ô tô quay đầu tại vị trí đặt biển; các phương tiện khác không bị cấm."},
    "P.124c": {"name": "Cấm rẽ trái và quay đầu xe", "meaning": "Cấm đồng thời hành vi rẽ trái và quay đầu xe tại vị trí đặt biển."},
    "P.124d": {"name": "Cấm rẽ phải và quay đầu xe", "meaning": "Cấm đồng thời hành vi rẽ phải và quay đầu xe tại vị trí đặt biển."},
    "P.124e": {"name": "Cấm ô tô rẽ trái và quay đầu xe", "meaning": "Cấm riêng xe ô tô rẽ trái và quay đầu xe tại vị trí đặt biển."},
    "P.124f": {"name": "Cấm ô tô rẽ phải và quay đầu xe", "meaning": "Cấm riêng xe ô tô rẽ phải và quay đầu xe tại vị trí đặt biển."},
    "P.125": {"name": "Cấm vượt", "meaning": "Cấm các loại xe cơ giới vượt nhau (trừ xe máy 2 bánh, xe gắn máy) trên đoạn đường đặt biển vì lý do an toàn (tầm nhìn hạn chế, đường hẹp...)."},
    "P.126": {"name": "Cấm xe ô tô tải vượt", "meaning": "Cấm riêng xe ô tô tải vượt xe cơ giới khác trên đoạn đường đặt biển."},
    "P.127": {"name": "Tốc độ tối đa cho phép", "meaning": "Báo tốc độ tối đa cho phép (km/h) mà các xe cơ giới không được vượt quá khi đi trên đoạn đường đặt biển."},
    "P.127a": {"name": "Tốc độ tối đa cho phép về ban đêm", "meaning": "Báo tốc độ tối đa cho phép áp dụng riêng vào ban đêm (thường từ 22h-6h), có thể khác với tốc độ ban ngày."},
    "P.127b": {"name": "Biển ghép tốc độ tối đa cho phép trên từng làn đường", "meaning": "Quy định tốc độ tối đa cho phép riêng cho từng làn đường, thể hiện dưới dạng biển ghép nhiều ô số."},
    "P.127c": {"name": "Biển ghép tốc độ tối đa theo phương tiện, trên từng làn", "meaning": "Quy định tốc độ tối đa cho phép khác nhau theo từng loại phương tiện và từng làn đường cụ thể."},
    "DP.127": {"name": "Hết tốc độ tối đa cho phép trên biển ghép", "meaning": "Báo hiệu hết hiệu lực của biển hạn chế tốc độ tối đa đã đặt trước đó trên biển ghép."},
    "P.128": {"name": "Cấm sử dụng còi", "meaning": "Cấm các loại xe sử dụng còi trong phạm vi biển có hiệu lực (thường ở khu vực bệnh viện, trường học, khu dân cư)."},
    "P.129": {"name": "Kiểm tra", "meaning": "Báo hiệu nơi phải dừng xe để cơ quan chức năng kiểm tra (hải quan, kiểm dịch, cân tải trọng...)."},
    "P.130": {"name": "Cấm dừng xe và đỗ xe", "meaning": "Cấm các loại xe dừng và đỗ ở phía đường có đặt biển, trừ xe được ưu tiên đang làm nhiệm vụ."},
    "P.131a": {"name": "Cấm đỗ xe", "meaning": "Cấm các loại xe đỗ (dừng lâu hoặc rời khỏi vô lăng) ở phía đường có đặt biển; xe được phép dừng tạm để đón/trả khách hoặc bốc dỡ hàng nhanh."},
    "P.131b": {"name": "Cấm đỗ xe ngày lẻ", "meaning": "Cấm đỗ xe vào các ngày lẻ trong tháng ở phía đường đặt biển."},
    "P.131c": {"name": "Cấm đỗ xe ngày chẵn", "meaning": "Cấm đỗ xe vào các ngày chẵn trong tháng ở phía đường đặt biển."},
    "P.132": {"name": "Nhường đường cho xe cơ giới đi ngược chiều qua đường hẹp", "meaning": "Báo cho lái xe biết phải nhường đường cho xe cơ giới đi ngược chiều tại các đoạn đường hẹp, đường qua cầu hẹp."},
    "DP.133": {"name": "Hết cấm vượt", "meaning": "Báo hiệu hết đoạn đường có hiệu lực của biển cấm vượt (P.125/P.126) đã đặt trước đó."},
    "DP.134": {"name": "Hết tốc độ tối đa cho phép", "meaning": "Báo hiệu hết hiệu lực của biển hạn chế tốc độ tối đa đã đặt trước đó, cho phép chạy trở lại theo tốc độ quy định chung."},
    "DP.135": {"name": "Hết tất cả các lệnh cấm", "meaning": "Báo hiệu hết tất cả hiệu lực các biển báo cấm (trừ các biển cấm dừng, đỗ xe) đã đặt trước đó trên cùng đoạn đường."},
    "P.136": {"name": "Cấm đi thẳng", "meaning": "Cấm các loại xe đi thẳng tại vị trí đặt biển; xe phải rẽ theo hướng khác."},
    "P.137": {"name": "Cấm rẽ trái, rẽ phải", "meaning": "Cấm các loại xe rẽ trái và rẽ phải tại vị trí đặt biển, chỉ được đi thẳng hoặc quay đầu (nếu không có biển cấm khác)."},
    "P.138": {"name": "Cấm đi thẳng, rẽ trái", "meaning": "Cấm các loại xe đi thẳng và rẽ trái tại vị trí đặt biển; xe chỉ được rẽ phải."},
    "P.139": {"name": "Cấm đi thẳng, rẽ phải", "meaning": "Cấm các loại xe đi thẳng và rẽ phải tại vị trí đặt biển; xe chỉ được rẽ trái."},
    "P.140": {"name": "Cấm xe công nông và các loại xe tương tự", "meaning": "Cấm xe công nông và các loại xe tự chế tương tự đi vào đoạn đường đặt biển."},

    # ------------------------------------------------------------------ #
    # NHÓM W — BIỂN BÁO NGUY HIỂM VÀ CẢNH BÁO (Chương 5, Phụ lục C)
    # ------------------------------------------------------------------ #
    "W.201a": {"name": "Chỗ ngoặt nguy hiểm", "meaning": "Báo trước sắp đến một chỗ ngoặt nguy hiểm (vòng cua) phía trước, cần giảm tốc độ và chú ý."},
    "W.201b": {"name": "Chỗ ngoặt nguy hiểm", "meaning": "Báo trước sắp đến một chỗ ngoặt nguy hiểm (vòng cua, hướng ngược lại với W.201a) phía trước."},
    "W.201c": {"name": "Chỗ ngoặt nguy hiểm có nguy cơ lật xe", "meaning": "Báo chỗ ngoặt nguy hiểm kèm nguy cơ lật xe nếu chạy quá tốc độ, cần giảm tốc độ mạnh."},
    "W.201d": {"name": "Chỗ ngoặt nguy hiểm có nguy cơ lật xe", "meaning": "Báo chỗ ngoặt nguy hiểm (hướng ngược lại) kèm nguy cơ lật xe nếu chạy quá tốc độ."},
    "W.202a": {"name": "Nhiều chỗ ngoặt nguy hiểm liên tiếp", "meaning": "Báo phía trước có từ hai chỗ ngoặt nguy hiểm trở lên liên tiếp nhau, ngoặt đầu tiên cùng hướng biển."},
    "W.202b": {"name": "Nhiều chỗ ngoặt nguy hiểm liên tiếp", "meaning": "Báo phía trước có từ hai chỗ ngoặt nguy hiểm trở lên liên tiếp nhau, ngoặt đầu tiên ngược hướng biển."},
    "W.203a": {"name": "Đường bị thu hẹp cả hai bên", "meaning": "Báo phía trước đường bị thu hẹp cả hai bên so với bề rộng của đường, cần chú ý giảm tốc độ."},
    "W.203b": {"name": "Đường bị thu hẹp bên trái", "meaning": "Báo phía trước đường bị thu hẹp về phía bên trái."},
    "W.203c": {"name": "Đường bị thu hẹp bên phải", "meaning": "Báo phía trước đường bị thu hẹp về phía bên phải."},
    "W.204": {"name": "Đường hai chiều", "meaning": "Báo sắp đến đoạn đường hai chiều (do trước và sau đoạn này là đường một chiều), cần chạy đúng phần đường của mình."},
    "W.205a": {"name": "Đường giao nhau", "meaning": "Báo trước sắp đến nơi đường giao nhau cùng mức dạng ngã ba, ngã tư kiểu chữ thập."},
    "W.205b": {"name": "Đường giao nhau", "meaning": "Báo trước sắp đến nơi đường giao nhau kiểu ngã ba bên phải."},
    "W.205c": {"name": "Đường giao nhau", "meaning": "Báo trước sắp đến nơi đường giao nhau kiểu ngã ba bên trái."},
    "W.205d": {"name": "Đường giao nhau", "meaning": "Báo trước sắp đến nơi đường giao nhau dạng chữ Y hoặc kiểu khác."},
    "W.205e": {"name": "Đường giao nhau", "meaning": "Báo trước sắp đến nơi đường giao nhau dạng đặc biệt (kiểu chạc nhiều nhánh)."},
    "W.206": {"name": "Giao nhau chạy theo vòng xuyến", "meaning": "Báo trước nơi giao nhau có bố trí đảo an toàn ở giữa nút giao, các xe phải đi vòng theo đảo (bùng binh)."},
    "W.207": {"name": "Giao nhau với đường không ưu tiên", "meaning": "Báo trước nơi đường giao nhau với đường nhánh (đường không ưu tiên); xe trên đường chính được ưu tiên đi trước."},
    "W.208": {"name": "Giao nhau với đường ưu tiên", "meaning": "Báo trước nơi giao nhau với đường ưu tiên (đường chính); xe trên đường đặt biển phải nhường đường cho xe trên đường ưu tiên."},
    "W.209": {"name": "Giao nhau có tín hiệu đèn", "meaning": "Báo trước nơi giao nhau có sử dụng đèn tín hiệu giao thông để điều khiển, cần chú ý giảm tốc độ."},
    "W.210": {"name": "Giao nhau với đường sắt có rào chắn", "meaning": "Báo trước nơi giao nhau giữa đường bộ và đường sắt có bố trí rào chắn (barie) tự động hoặc do người điều khiển."},
    "W.211a": {"name": "Giao nhau với đường sắt không có rào chắn", "meaning": "Báo trước nơi giao nhau với đường sắt không có rào chắn, cần giảm tốc độ và quan sát kỹ trước khi qua."},
    "W.211b": {"name": "Giao nhau với đường tàu điện", "meaning": "Báo trước nơi giao nhau giữa đường bộ với đường tàu điện (đường ray trên mặt đường)."},
    "W.212": {"name": "Cầu hẹp", "meaning": "Báo trước sắp đến cầu có bề rộng hẹp hơn so với đường, cần giảm tốc độ khi qua cầu."},
    "W.213": {"name": "Cầu tạm", "meaning": "Báo trước sắp đến cầu tạm (kết cấu tạm thời, chưa kiên cố), cần giảm tốc độ và chú ý tải trọng."},
    "W.214": {"name": "Cầu quay - Cầu cất", "meaning": "Báo trước sắp đến cầu có thể quay hoặc cất lên để tàu thuyền qua lại, cần chú ý tín hiệu đóng/mở cầu."},
    "W.215a": {"name": "Kè, vực sâu phía trước", "meaning": "Báo trước phía trước là khu vực có kè, vực hoặc vách sâu nguy hiểm, cần đặc biệt chú ý và giảm tốc độ."},
    "W.215b": {"name": "Kè, vực sâu bên đường phía bên phải", "meaning": "Báo bên phải đường có kè hoặc vực sâu nguy hiểm."},
    "W.215c": {"name": "Kè, vực sâu bên đường phía bên trái", "meaning": "Báo bên trái đường có kè hoặc vực sâu nguy hiểm."},
    "W.216a": {"name": "Đường ngầm", "meaning": "Báo trước sắp đến đoạn đường ngầm (đường tràn qua sông, suối), có thể ngập nước khi mưa lũ."},
    "W.216b": {"name": "Đường ngầm có nguy cơ lũ quét", "meaning": "Báo trước đoạn đường ngầm có nguy cơ xảy ra lũ quét bất ngờ, cần đặc biệt cẩn trọng vào mùa mưa."},
    "W.217": {"name": "Bến phà", "meaning": "Báo trước sắp đến bến phà, cần giảm tốc độ và chuẩn bị dừng chờ theo hướng dẫn."},
    "W.218": {"name": "Cửa chui", "meaning": "Báo trước sắp đến cửa hầm hoặc cửa chui có giới hạn không gian, cần chú ý chiều cao và bề rộng cho phép."},
    "W.219": {"name": "Dốc xuống nguy hiểm", "meaning": "Báo trước sắp đến đoạn đường xuống dốc nguy hiểm, cần giảm tốc độ, kiểm tra phanh trước khi xuống dốc."},
    "W.220": {"name": "Dốc lên nguy hiểm", "meaning": "Báo trước sắp đến đoạn đường lên dốc nguy hiểm, cần chọn số phù hợp và giữ tốc độ ổn định."},
    "W.221a": {"name": "Đường lồi lõm", "meaning": "Báo trước đoạn đường có mặt đường lồi lõm, gập ghềnh (không bằng phẳng), cần giảm tốc độ."},
    "W.221b": {"name": "Đường có gồ giảm tốc", "meaning": "Báo trước đoạn đường có gờ/gồ giảm tốc nhân tạo, cần giảm tốc độ khi đi qua."},
    "W.222a": {"name": "Đường trơn", "meaning": "Báo trước đoạn đường dễ trơn trượt (do mưa, dầu loang, băng...), cần giảm tốc độ và tránh phanh gấp."},
    "W.222b": {"name": "Lề đường nguy hiểm", "meaning": "Báo trước đoạn đường có lề đường nguy hiểm (yếu, sụt lún, không ổn định)."},
    "W.223a": {"name": "Vách núi nguy hiểm", "meaning": "Báo trước đoạn đường có vách núi nguy hiểm bên đường (có thể sạt lở, đá rơi)."},
    "W.223b": {"name": "Vách núi nguy hiểm", "meaning": "Báo trước đoạn đường có vách núi nguy hiểm bên đường phía đối diện."},
    "W.224": {"name": "Đường người đi bộ cắt ngang", "meaning": "Báo trước phía trước có đoạn đường dành cho người đi bộ cắt ngang qua đường, cần giảm tốc độ nhường đường cho người đi bộ."},
    "W.225": {"name": "Trẻ em", "meaning": "Báo trước tình huống nguy hiểm phía trước thường có trẻ em đi lại (gần trường học, khu vui chơi), lái xe cần giảm tốc độ và chủ động phòng ngừa."},
    "W.226": {"name": "Đường người đi xe đạp cắt ngang", "meaning": "Báo trước phía trước có đoạn đường dành cho xe đạp cắt ngang qua đường."},
    "W.227": {"name": "Công trường", "meaning": "Báo trước phía trước có công trường đang thi công trên đường, cần giảm tốc độ và chú ý biển báo phụ, rào chắn."},
    "W.228a": {"name": "Đá lở", "meaning": "Báo trước đoạn đường có hiện tượng đá lở từ ta luy dương xuống mặt đường, nguy hiểm cho xe cộ."},
    "W.228b": {"name": "Đá lở", "meaning": "Báo trước đoạn đường có hiện tượng đá lở (kiểu bố trí khác) từ taluy xuống mặt đường."},
    "W.228c": {"name": "Sỏi đá bắn lên", "meaning": "Báo trước đoạn đường có mặt đường rải sỏi đá dễ bắn lên khi xe chạy qua, cần giảm tốc độ."},
    "W.228d": {"name": "Nền đường yếu", "meaning": "Báo trước đoạn đường có nền đường yếu, dễ sụt lún, cần giảm tốc độ và đi cẩn thận."},
    "W.229": {"name": "Dải máy bay lên xuống", "meaning": "Báo trước đoạn đường cắt ngang qua khu vực máy bay lên xuống, cần đặc biệt chú ý quan sát."},
    "W.230": {"name": "Gia súc", "meaning": "Báo trước đoạn đường có thể có gia súc đi qua hoặc đi trên đường, cần giảm tốc độ và chú ý quan sát."},
    "W.231": {"name": "Thú rừng vượt qua đường", "meaning": "Báo trước đoạn đường (thường gần rừng, khu bảo tồn) có thể có thú rừng bất ngờ băng qua đường."},
    "W.232": {"name": "Gió ngang", "meaning": "Báo trước đoạn đường thường có gió ngang mạnh (cầu lớn, đèo cao), cần giữ chắc tay lái."},
    "W.233": {"name": "Nguy hiểm khác", "meaning": "Báo trước các trường hợp nguy hiểm khác trên đường mà không có biển báo cụ thể tương ứng."},
    "W.234": {"name": "Giao nhau với đường hai chiều", "meaning": "Báo trước xe đang đi trên đường một chiều sắp giao với đường hai chiều, cần chú ý xe đi ngược lại."},
    "W.235": {"name": "Đường đôi", "meaning": "Báo trước sắp vào đoạn đường đôi (có dải phân cách giữa), báo hiệu thay đổi từ đường hai chiều thông thường."},
    "W.236": {"name": "Kết thúc đường đôi", "meaning": "Báo trước đoạn đường đôi sắp kết thúc, chuyển sang đường hai chiều thông thường (không có dải phân cách)."},
    "W.237": {"name": "Cầu vồng", "meaning": "Báo trước sắp đến cầu có độ dốc cong dạng vồng, hạn chế tầm nhìn, cần giảm tốc độ."},
    "W.238": {"name": "Đường cao tốc phía trước", "meaning": "Báo trước phía trước là đoạn nhập vào đường cao tốc, cần chuẩn bị tăng tốc độ hòa nhập dòng xe an toàn."},
    "W.239a": {"name": "Đường cáp điện ở phía trên", "meaning": "Báo phía trên đường có đường dây cáp điện cao thế đi qua, cần chú ý với các xe có chiều cao lớn."},
    "W.239b": {"name": "Chiều cao tĩnh không thực tế", "meaning": "Báo chiều cao tĩnh không thực tế của công trình phía trên đường (cầu vượt, đường dây...) mà xe phải tuân thủ."},
    "W.240": {"name": "Đường hầm", "meaning": "Báo trước sắp vào đường hầm, cần bật đèn và giảm tốc độ theo quy định khi vào hầm."},
    "W.241": {"name": "Ùn tắc giao thông", "meaning": "Báo trước đoạn đường thường xuyên xảy ra ùn tắc giao thông, cần chủ động giảm tốc độ và giữ khoảng cách an toàn."},
    "W.242a": {"name": "Nơi đường sắt giao vuông góc với đường bộ", "meaning": "Báo trước nơi đường sắt cắt vuông góc với đường bộ, không có người gác hay rào chắn."},
    "W.242b": {"name": "Nơi đường sắt giao vuông góc với đường bộ", "meaning": "Báo trước nơi đường sắt cắt vuông góc với đường bộ (biến thể bố trí biển khác)."},
    "W.243a": {"name": "Nơi đường sắt giao không vuông góc với đường bộ", "meaning": "Báo trước nơi đường sắt giao cắt xiên góc (không vuông góc) với đường bộ."},
    "W.243b": {"name": "Nơi đường sắt giao không vuông góc với đường bộ", "meaning": "Báo trước nơi đường sắt giao cắt xiên góc với đường bộ (biến thể hướng khác)."},
    "W.243c": {"name": "Nơi đường sắt giao không vuông góc với đường bộ", "meaning": "Báo trước nơi đường sắt giao cắt xiên góc với đường bộ (biến thể bố trí khác)."},
    "W.244": {"name": "Đoạn đường hay xảy ra tai nạn", "meaning": "Báo trước đoạn đường thường xảy ra tai nạn giao thông, cần đặc biệt chú ý quan sát và giảm tốc độ."},
    "W.245a": {"name": "Đi chậm", "meaning": "Báo hiệu yêu cầu người tham gia giao thông phải đi chậm lại do phía trước có tình huống cần chú ý đặc biệt."},
    "W.245b": {"name": "Đi chậm", "meaning": "Báo hiệu yêu cầu đi chậm lại, có kèm chỉ dẫn thêm bằng tiếng Anh cho khách nước ngoài."},
    "W.246a": {"name": "Chú ý chướng ngại vật", "meaning": "Báo trước phía trước có chướng ngại vật cần né tránh (do chia hai dòng xe cùng chiều)."},
    "W.246b": {"name": "Chú ý chướng ngại vật", "meaning": "Báo trước phía trước có chướng ngại vật, hướng đi vòng chướng ngại vật bên trái."},
    "W.246c": {"name": "Chú ý chướng ngại vật", "meaning": "Báo trước phía trước có chướng ngại vật, hướng đi vòng chướng ngại vật bên phải."},
    "W.247": {"name": "Chú ý xe đỗ", "meaning": "Báo trước đoạn đường thường có xe đỗ bên đường, cần chú ý quan sát và giảm tốc độ."},

    # ------------------------------------------------------------------ #
    # NHÓM R — BIỂN HIỆU LỆNH (Chương 6, Phụ lục D)
    # ------------------------------------------------------------------ #
    "R.301a": {"name": "Hướng đi phải theo (đi thẳng)", "meaning": "Bắt buộc các loại xe (trừ xe ưu tiên) phải đi thẳng theo hướng mũi tên chỉ trên biển."},
    "R.301b": {"name": "Hướng đi phải theo (rẽ phải)", "meaning": "Bắt buộc các loại xe (trừ xe ưu tiên) phải rẽ phải theo hướng mũi tên chỉ trên biển."},
    "R.301c": {"name": "Hướng đi phải theo (rẽ trái)", "meaning": "Bắt buộc các loại xe (trừ xe ưu tiên) phải rẽ trái theo hướng mũi tên chỉ trên biển."},
    "R.301d": {"name": "Hướng đi phải theo (rẽ phải)", "meaning": "Bắt buộc các loại xe phải theo hướng rẽ phải quy định (biến thể vị trí đặt biển khác R.301b)."},
    "R.301e": {"name": "Hướng đi phải theo (rẽ trái)", "meaning": "Bắt buộc các loại xe phải theo hướng rẽ trái quy định (biến thể vị trí đặt biển khác R.301c)."},
    "R.301f": {"name": "Hướng đi phải theo (đi thẳng hoặc rẽ phải)", "meaning": "Bắt buộc xe chỉ được đi thẳng hoặc rẽ phải tại vị trí đặt biển."},
    "R.301g": {"name": "Hướng đi phải theo (đi thẳng hoặc rẽ trái)", "meaning": "Bắt buộc xe chỉ được đi thẳng hoặc rẽ trái tại vị trí đặt biển."},
    "R.301h": {"name": "Hướng đi phải theo (rẽ trái hoặc rẽ phải)", "meaning": "Bắt buộc xe chỉ được rẽ trái hoặc rẽ phải tại vị trí đặt biển, không được đi thẳng."},
    "R.302a": {"name": "Hướng phải đi vòng chướng ngại vật (bên phải)", "meaning": "Bắt buộc xe phải đi vòng sang bên phải để tránh chướng ngại vật phía trước."},
    "R.302b": {"name": "Hướng phải đi vòng chướng ngại vật (bên trái)", "meaning": "Bắt buộc xe phải đi vòng sang bên trái để tránh chướng ngại vật phía trước."},
    "R.302c": {"name": "Hướng phải đi vòng chướng ngại vật (hai bên)", "meaning": "Cho phép xe đi vòng chướng ngại vật ở cả hai phía (trái hoặc phải) tùy chọn."},
    "R.303": {"name": "Nơi giao nhau chạy theo vòng xuyến", "meaning": "Bắt buộc các xe khi qua nơi giao nhau phải chạy vòng theo đảo an toàn ở giữa (theo chiều mũi tên) - bùng binh."},
    "R.304": {"name": "Đường dành cho xe thô sơ", "meaning": "Báo đường dành riêng cho xe thô sơ (kể cả xe đạp) và người đi bộ, xe cơ giới không được đi vào."},
    "R.305": {"name": "Đường dành cho người đi bộ", "meaning": "Báo đường/lối đi dành riêng cho người đi bộ, các loại xe không được đi vào."},
    "R.411": {"name": "Hướng đi trên mỗi làn đường phải theo", "meaning": "Chỉ dẫn hướng đi bắt buộc cho từng làn đường cụ thể tại nơi đường giao nhau, mỗi làn phải đi theo đúng hướng mũi tên tương ứng."},
    "R.412a": {"name": "Làn đường dành cho xe ô tô khách", "meaning": "Báo làn đường dành riêng cho xe ô tô khách (kể cả xe buýt) lưu thông."},
    "R.412b": {"name": "Làn đường dành cho xe ô tô con", "meaning": "Báo làn đường dành riêng cho xe ô tô con lưu thông."},
    "R.412c": {"name": "Làn đường dành cho xe ô tô tải", "meaning": "Báo làn đường dành riêng cho xe ô tô tải lưu thông."},
    "R.412d": {"name": "Làn đường dành cho xe buýt", "meaning": "Báo làn đường dành riêng cho xe buýt lưu thông, các xe khác không được đi vào trừ trường hợp được phép."},
    "R.412e": {"name": "Làn đường dành cho xe máy", "meaning": "Báo làn đường dành riêng cho xe mô tô, xe máy lưu thông."},
    "R.412f": {"name": "Làn đường dành cho xe máy và xe đạp", "meaning": "Báo làn đường dành riêng cho cả xe máy và xe đạp lưu thông."},
    "R.412g": {"name": "Làn đường dành cho xe đạp", "meaning": "Báo làn đường dành riêng cho xe đạp lưu thông."},
    "R.412h": {"name": "Làn đường dành cho xe máy kéo", "meaning": "Báo làn đường dành riêng cho xe máy kéo lưu thông."},
    "R.413a": {"name": "Bắt đầu làn đường ô tô khách", "meaning": "Báo bắt đầu đoạn làn đường dành riêng cho xe ô tô khách."},
    "R.413b": {"name": "Bắt đầu làn đường ô tô con", "meaning": "Báo bắt đầu đoạn làn đường dành riêng cho xe ô tô con."},
    "R.415": {"name": "Biển gộp làn đường theo phương tiện", "meaning": "Biển hiệu lệnh gộp thể hiện quy định về làn đường cho nhiều loại phương tiện khác nhau trên cùng một mặt biển."},
    "R.420": {"name": "Bắt đầu khu đông dân cư", "meaning": "Báo bắt đầu đoạn đường đi vào khu vực đông dân cư, các phương tiện phải tuân theo tốc độ tối đa quy định trong khu đông dân cư."},
    "R.421": {"name": "Hết khu đông dân cư", "meaning": "Báo hết đoạn đường qua khu đông dân cư, các phương tiện được đi theo tốc độ tối đa ngoài khu đông dân cư."},
    "R.434": {"name": "Bến xe buýt", "meaning": "Báo hiệu vị trí bến (điểm dừng, đỗ) dành cho xe buýt đón trả khách; các xe khác không được dừng, đỗ tại vị trí này."},
    "R.443": {"name": "Làn đường cứu nạn", "meaning": "Báo hiệu vị trí làn đường/khu vực dành riêng cho xe cứu nạn, cứu hộ khẩn cấp."},

    # ------------------------------------------------------------------ #
    # NHÓM S — BIỂN CHỈ DẪN / BIỂN PHỤ (Chương 7-8, Phụ lục E/F)
    # ------------------------------------------------------------------ #
    "S.501": {"name": "Phạm vi tác dụng của biển", "meaning": "Biển phụ thông báo chiều dài đoạn đường nguy hiểm/cấm/hạn chế mà biển chính phía trên có hiệu lực."},
    "S.502": {"name": "Khoảng cách đến đối tượng báo hiệu", "meaning": "Biển phụ ghi khoảng cách thực tế từ vị trí đặt biển đến đối tượng cần báo hiệu (nơi nguy hiểm, nơi cấm...)."},
    "S.503": {"name": "Hướng tác dụng của biển", "meaning": "Biển phụ chỉ rõ hướng (trái/phải/cả hai) mà biển chính phía trên có hiệu lực áp dụng."},
    "S.507": {"name": "Hướng rẽ", "meaning": "Biển chỉ dẫn hướng rẽ tại các đoạn đường cong nguy hiểm hoặc đảo an toàn nơi giao nhau, giúp lái xe định hướng."},
    "S.508": {"name": "Biểu thị thời gian", "meaning": "Biển phụ ghi khung thời gian (giờ, ngày) mà biển chính phía trên có hiệu lực áp dụng."},
    "S.509a": {"name": "Chiều cao an toàn", "meaning": "Biển phụ bổ sung cho biển cảnh báo đường dây điện trên cao (W.239), chỉ rõ chiều cao an toàn để các phương tiện đi qua."},
    "S.509b": {"name": "Cấm đỗ xe (biển phụ)", "meaning": "Biển phụ bổ sung làm rõ ý nghĩa cho biển P.130/P.131 (cấm dừng, đỗ hoặc cấm đỗ xe) phía trên."},
    "S.510": {"name": "Biển ghi tên đường, tên khu vực", "meaning": "Biển chỉ dẫn cung cấp thông tin tên đường, tên địa danh, khu vực hành chính cho người tham gia giao thông."},
}


# Mô tả mặc định theo NHÓM biển, dùng khi mã biển cụ thể chưa có trong SIGN_INFO
_GROUP_FALLBACK = {
    "P": "Biểu thị điều cấm mà người tham gia giao thông không được vi phạm khi đi qua khu vực đặt biển.",
    "DP": "Báo hiệu hết hiệu lực của một hoặc nhiều biển cấm đã đặt trước đó.",
    "W": "Báo trước cho người tham gia giao thông biết tính chất nguy hiểm phía trước để chủ động phòng ngừa, giảm tốc độ.",
    "R": "Báo hiệu lệnh bắt buộc mà người tham gia giao thông phải chấp hành khi đi qua khu vực đặt biển.",
    "S": "Cung cấp thông tin chỉ dẫn hoặc thuyết minh bổ sung cho biển báo chính đặt kèm theo.",
}

_GROUP_LABEL_FROM_PREFIX = {
    "P": "Biển cấm",
    "DP": "Biển cấm",
    "W": "Biển nguy hiểm",
    "R": "Biển hiệu lệnh",
    "S": "Biển chỉ dẫn",
}


def _prefix_of(class_name: str) -> str:
    """Lấy tiền tố nhóm từ mã biển, vd 'P.130' -> 'P', 'DP.135' -> 'DP'."""
    return class_name.split(".")[0]


def get_sign_info(class_name: str) -> dict:
    """
    Trả về dict {"name": <tên biển>, "meaning": <ý nghĩa chi tiết>} cho một mã biển.
    Nếu mã biển chưa có trong SIGN_INFO, trả về mô tả mặc định theo nhóm để
    giao diện luôn có nội dung hiển thị.
    """
    if class_name in SIGN_INFO:
        return SIGN_INFO[class_name]

    prefix = _prefix_of(class_name)
    group_label = _GROUP_LABEL_FROM_PREFIX.get(prefix, "Biển báo")
    fallback_meaning = _GROUP_FALLBACK.get(prefix, "Chưa có thông tin chi tiết cho mã biển này.")
    return {
        "name": class_name,
        "meaning": fallback_meaning + f" (Thuộc nhóm: {group_label}. Mã biển chưa có trong cơ sở dữ liệu chi tiết, hãy bổ sung vào src/sign_info.py nếu cần.)",
    }