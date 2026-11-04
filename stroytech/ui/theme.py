"""Understated local application theme."""
STYLE = '''<style>
    .stMainBlockContainer {max-width: 1040px; padding-top: 1.5rem; padding-bottom: 3rem;}
    h1 {font-size: 1.65rem !important; font-weight: 600 !important; letter-spacing: -.02em; padding-bottom: .3rem !important;}
    h2, h3 {font-size: 1.15rem !important; font-weight: 600 !important;}
    [data-testid="stVerticalBlock"] {gap: .75rem;}
    [data-testid="stTabs"] [role="tablist"] {gap: 1.5rem; margin-bottom: .75rem;}
    [data-testid="stTabs"] [role="tab"] {font-weight: 500;}
    [data-testid="stExpander"] {border-radius: 5px;}
    [data-testid="stButton"] button, [data-testid="stFormSubmitButton"] button {border-radius: 5px; font-weight: 500;}
    [data-baseweb="select"] > div, [data-baseweb="input"] {border-radius: 5px;}
    hr {margin: 1rem 0;}
    @media (max-width: 640px) {
        .stMainBlockContainer {padding: 1rem 1rem 2rem;}
        h1 {font-size: 1.4rem !important;}
        [data-testid="stTabs"] [role="tablist"] {gap: 1rem;}
    }
    </style>'''
