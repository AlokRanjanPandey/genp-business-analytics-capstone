# ---------------- DATA LOADING ----------------
DATA_DIR = Path(__file__).parent

def load_csv(filename):
    path = DATA_DIR / filename

    if not path.exists():
        available_files = sorted(
            p.name for p in DATA_DIR.iterdir()
        )
        st.error(f"Missing file: {filename}")
        st.write("Files found beside app.py:", available_files)
        return pd.DataFrame()

    try:
        df = pd.read_csv(path)
        st.success(
            f"Loaded {filename}: {len(df)} rows"
        )
        return df
    except Exception as e:
        st.error(
            f"Could not read {filename}: {type(e).__name__}: {e}"
        )
        return pd.DataFrame()
