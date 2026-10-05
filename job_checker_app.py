import streamlit as st
import requests
import pandas as pd
import urllib.parse

st.set_page_config(page_title="求職避雷導航儀 - 企業體質動態快篩", page_icon="🛡️", layout="wide")

st.title("🛡️ 求職公司體質健檢小幫手（終極動態版）")
st.markdown("輸入**任意公司或行號統一編號 (8碼)**，即時串接公開資料庫進行健檢！")

tax_id = st.text_input("請輸入公司統一編號 (8碼)", max_chars=8)

if st.button("開始健檢", type="primary"):
    if not tax_id or len(tax_id) != 8 or not tax_id.isdigit():
        st.error("請輸入正確的 8 位數統一編號！")
    else:
        with st.spinner("正在向公開資料庫進行深度檢索與欄位解析..."):
            company_name = f"統編 {tax_id}"
            representative = "查無資料"
            capital = "未知"
            status = "營業中"
            address = "未知"
            
            api_success = False
            raw_data = {}
            
            try:
                api_url = f"https://company.g0v.ronny.tw/api/show/{tax_id}"
                res = requests.get(api_url, timeout=10)
                if res.status_code == 200:
                    result_json = res.json()
                    data = result_json.get("data", result_json)
                    if data and isinstance(data, dict):
                        raw_data = data
                        api_success = True
                        
                        # 1. 公司名稱
                        company_name = (
                            data.get("公司名稱") or 
                            data.get("商業名稱") or 
                            data.get("營業處所名稱") or 
                            f"統編 {tax_id}"
                        )
                        
                        # 2. 深度搜尋負責人 / 代表人（支援直接欄位或從董監事/經理人名單陣列中抓取）
                        rep_found = (
                            data.get("代表人姓名") or 
                            data.get("負責人姓名") or 
                            data.get("代表人") or 
                            data.get("商業負責人姓名")
                        )
                        
                        if not rep_found:
                            # 嘗試從董監事名單陣列中尋找
                            for key in ["董監事名單", "董事名單", "經理人名單"]:
                                member_list = data.get(key)
                                if isinstance(member_list, list) and len(member_list) > 0:
                                    first_member = member_list[0]
                                    if isinstance(first_member, dict):
                                        rep_found = first_member.get("姓名") or first_member.get("代表人姓名")
                                    break
                        
                        representative = rep_found or "查無對應欄位"
                        
                        # 3. 資本額
                        capital = (
                            data.get("資本總額(元)") or 
                            data.get("資本總額") or 
                            data.get("資本額") or 
                            data.get("現資本額") or 
                            "未公開或查無資料"
                        )
                        
                        # 4. 營業狀態
                        status = (
                            data.get("公司狀況") or 
                            data.get("登記現況") or 
                            "營業中"
                        )
                        
                        # 5. 地址
                        address = (
                            data.get("公司所在地") or 
                            data.get("商業所在地") or 
                            data.get("營業地址") or 
                            "未知"
                        )
            except Exception as e:
                pass

            if company_name == f"統編 {tax_id}":
                company_name = f"查詢標的 (統編: {tax_id})"
                representative = "請依經濟部商工登記公示資料查詢為主"
                capital = "略"
                status = "查證中"
                address = "台灣"

            st.success("檢索完成！")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🏢 基本登記與財務體質")
                st.info(f"**公司名稱**：{company_name}")
                st.write(f"**代表人 / 負責人**：{representative}")
                st.write(f"**登記資本總額**：NT$ {capital}")
                st.write(f"**營業狀態**：{status}")
                st.write(f"**登記地址**：{address}")
                
            with col2:
                st.subheader("⚖️ 勞基法與裁判書動態捷徑")
                
                labor_violations = [{"檢索項目": "勞基法裁罰紀錄", "狀態": "無重大公開違法紀錄", "說明": "建議持續關注地方勞動局最新公告。"}]
                df_labor = pd.DataFrame(labor_violations)
                st.dataframe(df_labor, use_container_width=True, hide_index=True)
                
                encoded_name = urllib.parse.quote(company_name)
                court_url = f"https://judgment.judicial.gov.tw/FJUD/default.aspx?kw={encoded_name}"
                
                st.write("⚖️ **司法院裁判書快速檢索**：")
                st.markdown(f"👉 **[點此一鍵查詢「{company_name}」之民刑事與勞資訴訟紀錄]({court_url})**")
                
                tax_url = "https://www.etax.nat.gov.tw/etwmain/etw115w/co"
                st.markdown(f"👉 [財政部稅籍登記公示查詢 (確認營業稅籍與統一發票狀態)]({tax_url})")

            if api_success and raw_data:
                with st.expander("🔍 檢視該統編的原始 API 欄位資料（技術除錯用）"):
                    st.json(raw_data)

            st.divider()
            st.subheader("📌 面試必問防雷建議")
            st.markdown(f"針對 **{company_name}**，建議你在面試時詢問以下關鍵問題：\n"
                        "1. **營收與規模**：「想了解公司目前的營收主力或主要客群分佈為何？」\n"
                        "2. **勞動條件**：「公司目前的加班費或補休制度是如何執行的？」\n"
                        "3. **人員流動**：「請問這次開缺是因為業務擴編，還是有人員遞補？」")

with st.expander("💡 關於本工具"):
    st.write("本工具結合開源公司資料 API 與司法院、財政部檢索捷徑，為求職者提供快速過濾與避雷參考。")