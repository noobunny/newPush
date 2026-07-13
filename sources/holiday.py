from datetime import date, datetime
from zhdate import ZhDate

# 中国法定节假日列表（农历日期 + 节日名称）
# 格式: (农历月, 农历日, 节日名称, 公历年份偏移(默认0=当年))
HOLIDAYS = [
    (1, 1, "春节", 0),
    (1, 15, "元宵节", 0),
    (5, 5, "端午节", 0),
    (7, 7, "七夕", 0),
    (8, 15, "中秋节", 0),
    (9, 9, "重阳节", 0),
    (12, 30, "除夕", 0),  # 除夕可能29或30
]

# 公历固定节日
SOLAR_HOLIDAYS = [
    (1, 1, "元旦"),
    (2, 14, "情人节"),
    (3, 8, "妇女节"),
    (4, 5, "清明节"),     # 有时是4.4
    (5, 1, "劳动节"),
    (6, 1, "儿童节"),
    (10, 1, "国庆节"),
    (12, 25, "圣诞节"),
]


def get_lunar_info(dt: date = None) -> dict:
    """获取农历信息"""
    dt = dt or date.today()
    try:
        # zhdate 需要 datetime 对象
        dt_dt = datetime(dt.year, dt.month, dt.day)
        zhdate = ZhDate.from_datetime(dt_dt)
        return {
            "success": True,
            "lunar_month": zhdate.lunar_month,
            "lunar_day": zhdate.lunar_day,
            "lunar_year": zhdate.lunar_year,
            "lunar_chinese": str(zhdate),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_next_holiday(dt: date = None) -> dict:
    """计算距离下一个节日还有多少天"""
    dt = dt or date.today()
    today = dt
    best = None

    # 检查未来 400 天内的节日
    for offset in range(0, 400):
        check_date = date(today.year, today.month, today.day)
        # 简单加 offset
        from datetime import timedelta
        check_date = today + timedelta(days=offset)

        # 公历节日
        for m, d, name in SOLAR_HOLIDAYS:
            if check_date.month == m and check_date.day == d:
                cd_dt = datetime(check_date.year, check_date.month, check_date.day)
                zh = ZhDate.from_datetime(cd_dt)
                week_str = ["一", "二", "三", "四", "五", "六", "日"][check_date.weekday()]
                best = {
                    "name": name,
                    "date": str(check_date),
                    "days_away": offset,
                    "weekday": f"星期{week_str}",
                    "lunar": str(zh),
                }
                break

        if best and best["days_away"] == 0:
            break  # 今天就是节日，直接返回

        # 农历节日
        if not best or best["days_away"] > offset:
            for lm, ld, name, _ in HOLIDAYS:
                try:
                    h_date = ZhDate(check_date.year, lm, ld).to_datetime()
                    holiday_date = h_date.date()
                except Exception:
                    continue
                if check_date == holiday_date:
                    cd_dt = datetime(check_date.year, check_date.month, check_date.day)
                    week_str = ["一", "二", "三", "四", "五", "六", "日"][check_date.weekday()]
                    candidate = {
                        "name": name,
                        "date": str(check_date),
                        "days_away": offset,
                        "weekday": f"星期{week_str}",
                        "lunar": str(ZhDate.from_datetime(cd_dt)),
                    }
                    if best is None or candidate["days_away"] < best["days_away"]:
                        best = candidate

        if best and best["days_away"] == 0:
            break

    return best
