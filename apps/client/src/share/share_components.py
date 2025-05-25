"""
공유 관련 UI 컴포넌트들
"""
import streamlit as st
import streamlit.components.v1 as components
from urllib.parse import quote
from .share_utils import generate_share_url, generate_kakao_share_message, generate_email_content


def render_share_options(plan):
    """공유 옵션 렌더링"""
    st.markdown("### 🔗 공유하기")
    
    if 'share_action' not in st.session_state:
        st.session_state.share_action = None
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📋 링크 생성", key="generate_link"):
            st.session_state.share_action = "link"
    
    with col2:
        if st.button("📱 카카오톡 공유", key="kakao_share"):
            st.session_state.share_action = "kakao"
    
    with col3:
        if st.button("📧 이메일 전송", key="email_share"):
            st.session_state.share_action = "email"
    
    with col4:
        if st.button("📱 QR 코드", key="qr_share"):
            st.session_state.share_action = "qr"
    
    if st.session_state.share_action == "link":
        _render_link_share(plan)
    elif st.session_state.share_action == "kakao":
        _render_kakao_share(plan)
    elif st.session_state.share_action == "email":
        _render_email_share(plan)
    elif st.session_state.share_action == "qr":
        _render_qr_share(plan)
    
    if st.session_state.share_action:
        st.markdown("---")
        if st.button("🔄 다른 공유 방법 선택", key="reset_share"):
            st.session_state.share_action = None
            st.rerun()


def _render_link_share(plan):
    """링크 공유 렌더링"""
    share_url = generate_share_url(plan)
    if share_url:
        clipboard_js = f"""
        <div style="height: 50px; opacity: 0;">
            <script>
            document.addEventListener('DOMContentLoaded', function() {{
                setTimeout(function() {{
                    copyToClipboardAndShowDialog();
                }}, 50);
            }});
            
            if (document.readyState === 'complete' || document.readyState === 'interactive') {{
                setTimeout(function() {{
                    copyToClipboardAndShowDialog();
                }}, 50);
            }}
            
            function copyToClipboardAndShowDialog() {{
                const url = "{share_url}";
                
                if (navigator.clipboard && window.isSecureContext) {{
                    navigator.clipboard.writeText(url).then(function() {{
                        showSuccessDialog();
                    }}).catch(function(err) {{
                        console.log('Clipboard API 실패, execCommand 시도:', err);
                        fallbackCopyTextToClipboard(url);
                    }});
                }} else {{
                    fallbackCopyTextToClipboard(url);
                }}
            }}
            
            function fallbackCopyTextToClipboard(text) {{
                try {{
                    const textArea = document.createElement("textarea");
                    textArea.value = text;
                    textArea.style.position = "fixed";
                    textArea.style.top = "0";
                    textArea.style.left = "0";
                    textArea.style.width = "2em";
                    textArea.style.height = "2em";
                    textArea.style.padding = "0";
                    textArea.style.border = "none";
                    textArea.style.outline = "none";
                    textArea.style.boxShadow = "none";
                    textArea.style.background = "transparent";
                    textArea.style.fontSize = "16px"; 
                    
                    document.body.appendChild(textArea);
                    
                    if (navigator.userAgent.match(/ipad|iphone/i)) {{
                        const range = document.createRange();
                        range.selectNodeContents(textArea);
                        const selection = window.getSelection();
                        selection.removeAllRanges();
                        selection.addRange(range);
                        textArea.setSelectionRange(0, 999999);
                    }} else {{
                        textArea.select();
                        textArea.setSelectionRange(0, 999999);
                    }}
                    
                    const successful = document.execCommand('copy');
                    document.body.removeChild(textArea);
                    
                    if (successful) {{
                        showSuccessDialog();
                    }} 
                }} catch (err) {{
                    console.log('execCommand 실패:', err);
                }}
            }}
            
            function showSuccessDialog() {{
                showDialog('✅ 링크가 복사되었습니다!', 'rgba(40, 167, 69, 0.9)');
            }}
            
            function showDialog(message, bgColor, duration = 3000) {{
                const existingDialog = document.getElementById('copyDialog');
                if (existingDialog) {{
                    existingDialog.remove();
                }}
                
                const dialog = document.createElement('div');
                dialog.id = 'copyDialog';
                dialog.style.cssText = `
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: ${{bgColor}};
                    color: white;
                    padding: 20px 30px;
                    border-radius: 10px;
                    font-family: "Source Sans Pro", sans-serif;
                    font-size: 16px;
                    font-weight: 600;
                    z-index: 9999;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                    backdrop-filter: blur(10px);
                    text-align: center;
                    min-width: 250px;
                    max-width: 90vw;
                `;
                dialog.innerHTML = message;
                
                document.body.appendChild(dialog);
                
                setTimeout(function() {{
                    if (dialog && dialog.parentNode) {{
                        dialog.parentNode.removeChild(dialog);
                    }}
                }}, duration);
            }}
            </script>
        </div>
        """
        
        components.html(clipboard_js, height=50)
        
        st.markdown("**📋 공유 링크:**")
        st.code(share_url, language=None)
        
        st.info("💡 **Mac 사용자 안내**: 자동 복사가 실패할 경우, 위의 링크를 직접 선택하여 ⌘+C로 복사해주세요!")


def _render_kakao_share(plan):
    """카카오톡 공유 렌더링"""
    share_url = generate_share_url(plan)
    if share_url:
        kakao_message = generate_kakao_share_message(plan)
        
        kakao_js = f"""
        <div style="height: 50px; opacity: 0;">
            <script>
            document.addEventListener('DOMContentLoaded', function() {{
                setTimeout(function() {{
                    shareToKakao();
                }}, 50);
            }});
            
            if (document.readyState === 'complete' || document.readyState === 'interactive') {{
                setTimeout(function() {{
                    shareToKakao();
                }}, 50);
            }}
            
            function shareToKakao() {{
                const message = `{kakao_message.replace('`', '\\`').replace('"', '\\"')}`;
                const url = "{share_url}";
                const fullMessage = message + "\\n\\n" + url;
                
                if (navigator.share) {{
                    navigator.share({{
                        title: '여행 계획 공유',
                        text: message,
                        url: url
                    }}).then(() => {{
                        showSuccessDialog('✅ 공유가 완료되었습니다!');
                    }}).catch((error) => {{
                        console.log('Web Share API 실패:', error);
                        fallbackKakaoShare(fullMessage);
                    }});
                }} else {{
                    fallbackKakaoShare(fullMessage);
                }}
            }}
            
            function fallbackKakaoShare(message) {{
                if (navigator.clipboard && window.isSecureContext) {{
                    navigator.clipboard.writeText(message).then(function() {{
                        showKakaoDialog();
                    }}).catch(function(err) {{
                        fallbackCopyTextToClipboard(message);
                    }});
                }} else {{
                    fallbackCopyTextToClipboard(message);
                }}
            }}
            
            function fallbackCopyTextToClipboard(text) {{
                try {{
                    const textArea = document.createElement("textarea");
                    textArea.value = text;
                    textArea.style.position = "fixed";
                    textArea.style.top = "0";
                    textArea.style.left = "0";
                    textArea.style.width = "2em";
                    textArea.style.height = "2em";
                    textArea.style.padding = "0";
                    textArea.style.border = "none";
                    textArea.style.outline = "none";
                    textArea.style.boxShadow = "none";
                    textArea.style.background = "transparent";
                    textArea.style.fontSize = "16px";
                    
                    document.body.appendChild(textArea);
                    textArea.select();
                    textArea.setSelectionRange(0, 999999);
                    
                    const successful = document.execCommand('copy');
                    document.body.removeChild(textArea);
                    
                    if (successful) {{
                        showKakaoDialog();
                    }}
                }} catch (err) {{
                    console.log('복사 실패:', err);
                }}
            }}
            
            function showKakaoDialog() {{
                showDialog('📱 메시지가 복사되었습니다!<br>카카오톡에 붙여넣기 해주세요.', 'rgba(254, 229, 0, 0.9)', 4000);
            }}
            
            function showSuccessDialog(message) {{
                showDialog(message, 'rgba(40, 167, 69, 0.9)');
            }}
            
            function showDialog(message, bgColor, duration = 3000) {{
                const existingDialog = document.getElementById('shareDialog');
                if (existingDialog) {{
                    existingDialog.remove();
                }}
                
                const dialog = document.createElement('div');
                dialog.id = 'shareDialog';
                dialog.style.cssText = `
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: ${{bgColor}};
                    color: #333;
                    padding: 20px 30px;
                    border-radius: 10px;
                    font-family: "Source Sans Pro", sans-serif;
                    font-size: 16px;
                    font-weight: 600;
                    z-index: 9999;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                    backdrop-filter: blur(10px);
                    text-align: center;
                    min-width: 250px;
                    max-width: 90vw;
                `;
                dialog.innerHTML = message;
                
                document.body.appendChild(dialog);
                
                setTimeout(function() {{
                    if (dialog && dialog.parentNode) {{
                        dialog.parentNode.removeChild(dialog);
                    }}
                }}, duration);
            }}
            </script>
        </div>
        """
        
        components.html(kakao_js, height=50)
        
        st.markdown("**📱 카카오톡 공유 메시지:**")
        st.code(f"{kakao_message}\n\n{share_url}", language=None)
        
        st.info("💡 **모바일에서는 자동 공유**, **PC에서는 메시지가 복사**됩니다. 카카오톡에 붙여넣기 해주세요!")


def _render_email_share(plan):
    """이메일 공유 렌더링"""
    share_url = generate_share_url(plan)
    if share_url:
        subject, body = generate_email_content(plan)
        body_with_url = body.format(share_url=share_url)
        
        st.markdown("**📧 이메일로 공유하기:**")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("**제목:**")
        with col2:
            st.code(subject, language=None)
        
        st.text_area("이메일 본문", value=body_with_url, height=200, key="email_body")
        
        st.markdown("**📤 전송 방법을 선택하세요:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📧 이메일 앱 열기", key="open_email_app"):
                _render_email_app_opener(subject, body_with_url)
        
        with col2:
            if st.button("📄 본문 복사", key="copy_body"):
                _render_email_body_copier(body_with_url)
        
        st.markdown("---")
        
        st.markdown("**🌐 웹메일**")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&su={quote(subject)}&body={quote(body_with_url)}"
            if st.button("📧 Gmail", key="gmail_button"):
                components.html(f'<script>window.open("{gmail_url}", "_blank");</script>', height=0)
        
        with col2:
            naver_url = f"https://mail.naver.com/write?subject={quote(subject)}&body={quote(body_with_url)}"
            if st.button("📧 네이버", key="naver_button"):
                components.html(f'<script>window.open("{naver_url}", "_blank");</script>', height=0)
        
        with col3:
            daum_url = f"https://mail.daum.net/compose?subject={quote(subject)}&body={quote(body_with_url)}"
            if st.button("📧 다음", key="daum_button"):
                components.html(f'<script>window.open("{daum_url}", "_blank");</script>', height=0)
        
        with col4:
            outlook_url = f"https://outlook.live.com/mail/0/deeplink/compose?subject={quote(subject)}&body={quote(body_with_url)}"
            if st.button("📧 Outlook", key="outlook_button"):
                components.html(f'<script>window.open("{outlook_url}", "_blank");</script>', height=0)


def _render_qr_share(plan):
    """QR 코드 공유 렌더링"""
    share_url = generate_share_url(plan)
    if share_url:
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={quote(share_url)}"
        
        st.markdown("**📱 QR 코드로 공유하기:**")
        st.markdown("")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(qr_url, caption="QR 코드를 스캔하세요", width=280)
        
        st.markdown("")
        
        st.markdown("""
        **📱 사용 방법:**
        
        1. **스마트폰 카메라**로 QR 코드 스캔
        2. 또는 **카카오톡 QR 스캔** 기능 사용  
        3. 링크를 터치하여 여행 계획 확인
        
        **💡 팁:** QR 코드를 저장해서 나중에 공유할 수도 있어요!
        """)
        
        st.markdown("---")
        
        st.markdown("**🔗 공유 링크:**")
        st.code(share_url, language=None)
        
        download_qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&format=png&data={quote(share_url)}"
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.markdown(f"[📥 QR 코드 이미지 다운로드]({download_qr_url})")
        
        st.info("💡 **QR 코드를 스캔**하면 바로 여행 계획을 확인할 수 있습니다!")


def _render_email_app_opener(subject, body):
    """이메일 앱 열기 JavaScript"""
    email_js = f"""
    <div style="height: 50px; opacity: 0;">
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            setTimeout(function() {{
                openEmailApp();
            }}, 50);
        }});
        
        function openEmailApp() {{
            const subject = encodeURIComponent("{subject.replace('"', '\\"')}");
            const body = encodeURIComponent(`{body.replace('`', '\\`').replace('"', '\\"')}`);
            const mailtoLink = `mailto:?subject=${{subject}}&body=${{body}}`;
            
            try {{
                const link = document.createElement('a');
                link.href = mailtoLink;
                link.target = '_blank';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }} catch (error) {{
                console.log('이메일 앱 열기 실패:', error);
            }}
        }}
        </script>
    </div>
    """
    components.html(email_js, height=50)


def _render_email_body_copier(body):
    """이메일 본문 복사 JavaScript"""
    copy_body_js = f"""
    <div style="height: 50px; opacity: 0;">
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            setTimeout(function() {{
                copyBody();
            }}, 50);
        }});
        
        function copyBody() {{
            const body = `{body.replace('`', '\\`').replace('"', '\\"')}`;
            
            if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(body).then(function() {{
                    showDialog('✅ 본문이 복사되었습니다!', 'rgba(40, 167, 69, 0.9)');
                }}).catch(function(err) {{
                    fallbackCopy(body);
                }});
            }} else {{
                fallbackCopy(body);
            }}
        }}
        
        function fallbackCopy(text) {{
            const textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.style.position = "fixed";
            textArea.style.top = "0";
            textArea.style.left = "0";
            textArea.style.opacity = "0";
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            showDialog('✅ 본문이 복사되었습니다!', 'rgba(40, 167, 69, 0.9)');
        }}
        
        function showDialog(message, bgColor, duration = 3000) {{
            const existingDialog = document.getElementById('copyDialog');
            if (existingDialog) {{
                existingDialog.remove();
            }}
            
            const dialog = document.createElement('div');
            dialog.id = 'copyDialog';
            dialog.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: ${{bgColor}};
                color: white;
                padding: 20px 30px;
                border-radius: 10px;
                font-family: "Source Sans Pro", sans-serif;
                font-size: 16px;
                font-weight: 600;
                z-index: 9999;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                backdrop-filter: blur(10px);
                text-align: center;
                min-width: 250px;
                max-width: 90vw;
            `;
            dialog.innerHTML = message;
            
            document.body.appendChild(dialog);
            
            setTimeout(function() {{
                if (dialog && dialog.parentNode) {{
                    dialog.parentNode.removeChild(dialog);
                }}
            }}, duration);
        }}
        </script>
    </div>
    """
    components.html(copy_body_js, height=50) 