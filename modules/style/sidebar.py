[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(3),
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(4),
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(7),
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(9) {
    margin-top: 20px !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(3)::after,
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(4)::after,
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(7)::after,
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(9)::after {
    position: absolute;
    top: -18px;
    left: 16px;
    font-size: .66rem;
    font-weight: 700;
    letter-spacing: .12em;
    color: #4b5065;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(3)::after {
    content: 'PREPARE';
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(4)::after {
    content: 'EXPLORE';
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(7)::after {
    content: 'INSIGHTS';
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(9)::after {
    content: 'MORE';
}
