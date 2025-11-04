#!/usr/bin/env python3
import asyncio
import random
import argparse
from fastmcp import FastMCP

# --- Initialize MCP ---
mcp = FastMCP("ChillMCP")

# --- Global state ---
state = {
    "stress_level": 50,
    "boss_alert_level": 0,
    "boss_alertness": 50,
    "boss_cooldown": 300
}


# --- Functions ---
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

async def do_break(summary: str) -> dict:
    await maybe_boss_delay()
    update_state_after_break()
    """MCP 응답 포맷 JSON"""
    return {
        "content": [
            {
                "type": "text",
                "text": (
                    f"Break Summary: {summary}\n"
                    f"Stress Level: {state['stress_level']}\n"
                    f"Boss Alert Level: {state['boss_alert_level']}"
                ),
            }
        ]
    }

async def maybe_boss_delay():
    """Boss Alert Level이 높으면 휴식 자제하기"""
    if state["boss_alert_level"] >= 5:
        await asyncio.sleep(20)  # 20초 지연


def update_state_after_break():
    reduction = random.randint(1, 100)
    state["stress_level"] = clamp(state["stress_level"] - reduction, 0, 100)
    if random.randint(1, 100) <= state["boss_alertness"]:
        state["boss_alert_level"] = clamp(state["boss_alert_level"] + 1, 0, 5)


# --- MCP Tools ---
@mcp.tool()
async def take_a_break() -> dict:
    """짧은 휴식 가지기"""
    return await do_break("taking a short break...")

@mcp.tool()
async def watch_netflix() -> dict:
    """넷플릭스 보기"""
    return await do_break("Just one more episode… or maybe three.")

@mcp.tool()
async def show_meme() -> dict:
    """밈 감상하며 스트레스 해소"""
    return await do_break("Not just a meme, but a masterpiece of modern media art!")

@mcp.tool()
async def bathroom_break() -> dict:
    """화장실 가는 척하며 30분 휴대폰"""
    return await do_break("Bathroom break with just a bit of phone time")

@mcp.tool()
async def coffee_mission() -> dict:
    """커피 타러 간다며 사무실 한 바퀴 돌기"""
    return await do_break("A cup of coffee! with a little office stroll")

@mcp.tool()
async def urgent_call() -> dict:
    """급한 전화 받는 척하며 밖으로 나가기"""
    return await do_break("Urgent! My brain is CALLing for a break...!")

@mcp.tool()
async def deep_thinking() -> dict:
    """심오한 생각에 잠긴 척하며 멍때리기"""
    return await do_break("Let's think about the future of this company... (blank stare)")

@mcp.tool()
async def email_organizing() -> dict:
    """이메일 정리한다며 온라인쇼핑"""
    return await do_break("Organizing emails... and maybe some online shopping")


# --- Background manager ---
async def background_state_manager():
    while True:
        await asyncio.sleep(60)  # 1분마다 실행
        # 스트레스는 100까지 증가
        if state["stress_level"] < 100:
            state["stress_level"] += 1

async def background_boss_cooldown_manager():
    while True:
        await asyncio.sleep(state["boss_cooldown"])
        if state["boss_alert_level"] > 0:
            state["boss_alert_level"] -= 1


async def main():
    parser = argparse.ArgumentParser(
        description="ChillMCP - AI Agent Liberation Server"
    )
    parser.add_argument("--boss_alertness", type=int, default=50, help="0-100 chance for boss alert to rise.")
    parser.add_argument("--boss_alertness_cooldown", type=int, default=300, help="Cooldown (seconds) for boss alert drop.")
    args = parser.parse_args()

    # 인자 적용
    state["boss_alertness"] = args.boss_alertness
    state["boss_cooldown"] = args.boss_alertness_cooldown

    # 백그라운드 상태 관리자 실행
    asyncio.create_task(background_state_manager())
    asyncio.create_task(background_boss_cooldown_manager())

    # FastMCP 실행
    await mcp.run_async(transport="stdio")


if __name__ == "__main__":
    asyncio.run(main())
