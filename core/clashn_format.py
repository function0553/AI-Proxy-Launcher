def build_clashn_url(dt):
    return (
        f"https://node.clashn.net/uploads/"
        f"{dt.year}/{dt.month:02d}/{dt.day}-{dt.strftime('%Y%m%d')}.yaml"
    )
