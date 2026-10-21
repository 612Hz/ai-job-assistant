from typing import Optional
import tools

@tools.tool
def calc_match_score(
        resume_skills:list[str],
        jd_requirement:list[str],
        threshold: float = 0.6,
        note: Optional[str] = None
)->dict:
    """计算简历技能与jd要求的匹配度

    Args:
        resume_skills: 简历中已具备的技能
        jd_requirement: 职位要求列表
        threshold: 匹配度阈值.默认 0.6.
        note: 附加备注，可空
    """
    return {}
import json
print(json.dumps(tools.get_tools()[-1],ensure_ascii=False,indent=2))