# Coverage backlog — triaged candidates

Source: the 107 unpromoted stubs in `candidates.review.json` (Wikipedia lists), triaged
2026-07-06 per the street-sighting workflow in CLAUDE.md.

**2026-07-06: FULL SWEEP COMPLETED — all Tier A and Tier B dishes promoted (75 new
entries, dataset 80 → 155).** This file is now the ledger of what was decided.

## Promoted as full entries (75)

Soups & bowls: bò kho, canh chua, bún mọc, bún măng vịt, bún ốc, bún thang, miến lươn,
miến trộn, bún bung, cháo (generic entry + variants), súp măng cua, canh khoai mỡ,
ốc nấu chuối đậu, khổ qua nhồi thịt.

Street snacks & fried: bánh rán (aka bánh cam), bánh tiêu, chuối chiên, quẩy, bánh gối,
bánh đúc (3 variants), bánh tôm (Hồ Tây stub folded in as aka), chạo tôm, cơm cháy,
bánh cống, bánh khúc, bánh tẻ, bánh tai, bánh quai vạc, bánh đa nướng, cơm lam, cơm nắm.

Festival & ritual: bánh chưng, bánh tét, bánh giầy, bánh trung thu, bánh phu thê, bánh tro,
oản.

Mains, feast & charcuterie: bò 7 món, dồi (tiết/huyết/sụn), giò lụa (variants: giò thủ,
chả quế, giò bò), tiết canh (WITH explicit health warning in history), ốc bươu nhồi thịt,
gỏi cá trích (kept separate from gỏi cá Nam Ô — different island, different build), yến sào,
ô mai, cơm rượu (rượu nếp stub merged in as aka).

Sweets: bánh da lợn, bánh lọt, bánh chuối (hấp/nướng variants), bánh cốm, bánh đậu xanh,
bánh pía, bánh gai (kept separate from bánh ít lá gai; cross-referenced), bánh in, bánh khảo,
bánh mật, bánh nhãn, bánh cáy, bánh kẹp lá dứa, bánh rế, bánh tai heo, mè xửng, kẹo dừa,
sương sáo (aka sương sa), sâm bổ lượng.

Drinks: bia hơi, sữa đậu nành, rau má, chanh muối, soda hột gà, rượu cần, rượu đế,
rượu thuốc, rượu rắn (with tourist-trap/wildlife caveat).

## Resolved as alias/variant instead of entry

- Bánh trôi / bánh chay → variant + aka on chè trôi nước
- Cơm gà Quảng Nam / Tam Kỳ → variant on cơm gà Hội An
- Bánh tôm Hồ Tây → aka on bánh tôm
- Rượu nếp → aka on cơm rượu
- Bánh cam → aka on bánh rán

## Rejected (not dish entries) — unchanged from triage

- Condiments/sauces (nước mắm, mắm tôm, nước chấm, tương ớt, sa tế, muối ớt xanh/rau răm,
  hoisin, xì dầu, tương): components → future "sauces decoder" section, not dishes.json
- Generic/ingredient rows: rice vermicelli (bún), cellophane noodles, "Mì or Súp mì",
  "Món cuốn", "Congee cháo" (covered by the new cháo entry), chà bông/rousong (topping),
  "Cassava-based dishes" & "Bánh lá" & "Vietnamese wine" (umbrella rows)
- "Trà Việt": tea culture already carried by the trà đá entry; a proper tea-ceremony entry
  is out of decoder scope (menus don't need it decoded)
- Lò trấu: a rice-husk stove. Still not food.
- Duplicates: "Chả giò or Nem rán" (= chả giò), "Bò nướng lá lốt" (= bò lá lốt),
  "Bánh phu thê bột bán" (variant of bánh phu thê), second "Bánh rế" listing

## Still open

- Street sightings inbox: see `data/sightings.json` (trộn lộn xộn, "gan bu um")
- Images for the 75 new dishes: NOT yet sourced — all have `img_query` fallbacks.
  Run `find-images` + visual review in batches when wanted (expect Commons to have
  maybe half of these; the obscure village cakes will need own-photos or nothing).
- Eventual TasteAtlas name gap-check (facts only, no scraping) per roadmap.
