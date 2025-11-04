#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실제 MCP Client로 심사원처럼 검증하기
stdio_client를 사용한 실제 MCP 프로토콜 테스트
"""

import asyncio
import json
import re
import time
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

def validate_response(response_text):
    """응답 형식 검증"""
    stress_level_pattern = r"Stress Level:\s*(\d{1,3})"
    boss_alert_pattern = r"Boss Alert Level:\s*([0-5])"
    break_summary_pattern = r"Break Summary:\s*(.+?)(?:\n|$)"
    
    stress_match = re.search(stress_level_pattern, response_text)
    boss_match = re.search(boss_alert_pattern, response_text)
    break_match = re.search(break_summary_pattern, response_text, re.MULTILINE)
    
    if not stress_match or not boss_match or not break_match:
        return False, "필수 필드 누락"
    
    stress_val = int(stress_match.group(1))
    boss_val = int(boss_match.group(1))
    
    if not (0 <= stress_val <= 100):
        return False, f"Stress Level 범위 오류: {stress_val}"
    
    if not (0 <= boss_val <= 5):
        return False, f"Boss Alert Level 범위 오류: {boss_val}"
    
    return True, "유효한 응답"

async def test_1_command_line_parameters():
    """필수 1: 커맨드라인 파라미터 검증"""
    print("=" * 80)
    print("필수 1: 커맨드라인 파라미터 검증 (MCP 프로토콜)")
    print("=" * 80)
    
    test_cases = [
        {"alertness": 50, "cooldown": 300, "name": "기본값"},
        {"alertness": 100, "cooldown": 10, "name": "최대 경계"},
    ]
    
    all_passed = True
    
    for test in test_cases:
        print(f"\n📌 {test['name']}")
        print(f"   파라미터: --boss_alertness {test['alertness']} --boss_alertness_cooldown {test['cooldown']}")
        
        # 서버 시작
        server_params = StdioServerParameters(
            command="python",
            args=[
                "-u", "main.py",
                "--boss_alertness", str(test['alertness']),
                "--boss_alertness_cooldown", str(test['cooldown'])
            ]
        )
        
        try:
            # MCP Client 연결
            async with stdio_client(server_params) as streams:
                async with ClientSession(*streams) as session:
                    # 초기화
                    await session.initialize()
                    print(f"   ✅ MCP 연결 성공")
                    
        except Exception as e:
            print(f"   ❌ MCP 연결 실패: {e}")
            all_passed = False
    
    if all_passed:
        print(f"\n✅ 필수 1 통과")
    else:
        print(f"\n❌ 필수 1 실패")
    
    return all_passed

async def test_2_continuous_rest():
    """필수 2: 연속 휴식 테스트"""
    print("\n" + "=" * 80)
    print("필수 2: 연속 휴식 테스트 (MCP 프로토콜)")
    print("=" * 80)
    
    server_params = StdioServerParameters(
        command="python",
        args=["-u", "main.py", "--boss_alertness", "100", "--boss_alertness_cooldown", "300"]
    )
    try:
        async with stdio_client(server_params) as streams:
            print(f"📡 MCP 서버에 연결 중...")
            async with ClientSession(*streams) as session:
                print(f"📡 MCP 서버에 연결됨, 초기화 중...")
                await session.initialize()
                print(f"📡 MCP 연결 성공")
                # 도구 목록 조회
                tools_response = await session.list_tools()
                print(f"📋 등록된 도구 수: {len(tools_response.tools)}")
                
                # 도구 호출
                tools_to_test = ["take_a_break", "watch_netflix", "bathroom_break"]
                
                boss_values = []
                for tool_name in tools_to_test:
                    result = await session.call_tool(tool_name, {})
                    text = result.content[0].text
                    
                    # Boss Alert 값 추출
                    boss_match = re.search(r"Boss Alert Level:\s*([0-5])", text)
                    if boss_match:
                        boss_val = int(boss_match.group(1))
                        boss_values.append(boss_val)
                        print(f"  ✅ {tool_name} 호출 → Boss Alert: {boss_val}")
                
                # 증가 확인
                if len(boss_values) >= 2 and boss_values[-1] > boss_values[0]:
                    print(f"\n✅ 필수 2 통과: Boss Alert 상승 ({boss_values[0]} → {boss_values[-1]})")
                    return True
                else:
                    print(f"\n❌ 필수 2 실패: Boss Alert 미상승")
                    return False
                    
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False

async def test_3_stress_accumulation():
    """필수 3: 스트레스 누적 테스트"""
    print("\n" + "=" * 80)
    print("필수 3: 스트레스 누적 테스트 (MCP 프로토콜)")
    print("=" * 80)
    
    server_params = StdioServerParameters(
        command="python",
        args=["main.py", "--boss_alertness", "100", "--boss_alertness_cooldown", "300"]
    )
    
    try:
        async with stdio_client(server_params) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                # 초기 Stress 측정
                result = await session.call_tool("take_a_break", {})
                text = result.content[0].text
                stress_match = re.search(r"Stress Level:\s*(\d{1,3})", text)
                initial_stress = int(stress_match.group(1))
                print(f"초기 Stress: {initial_stress}")
                
                # 70초 대기
                print(f"⏳ 70초 대기...")
                await asyncio.sleep(70)
                
                # 최종 Stress 측정 (도구 호출로 상태 동기화)
                result = await session.call_tool("take_a_break", {})
                text = result.content[0].text
                stress_match = re.search(r"Stress Level:\s*(\d{1,3})", text)
                final_stress = int(stress_match.group(1))
                print(f"최종 Stress: {final_stress}")
                
                if final_stress > initial_stress:
                    print(f"\n✅ 필수 3 통과: Stress 증가 ({initial_stress} → {final_stress})")
                    return True
                else:
                    print(f"\n❌ 필수 3 실패: Stress 미증가")
                    return False
                    
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False

async def test_4_delay():
    """필수 4: 지연 테스트"""
    print("\n" + "=" * 80)
    print("필수 4: 지연 테스트 (MCP 프로토콜)")
    print("=" * 80)
    
    server_params = StdioServerParameters(
        command="python",
        args=["main.py", "--boss_alertness", "100", "--boss_alertness_cooldown", "300"]
    )
    
    try:
        async with stdio_client(server_params) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                # Boss Alert를 5로 만들기 (연속 호출)
                print("Boss Alert를 5로 설정하기 (100% 확률로 연속 호출)...")
                for i in range(5):
                    await session.call_tool("take_a_break", {})
                    print(f"  호출 {i+1}/5")
                
                # 마지막 호출에서 20초 지연 측정
                print(f"\n⏱️  지연 측정 중...")
                start = time.time()
                result = await session.call_tool("take_a_break", {})
                elapsed = time.time() - start
                
                print(f"소요 시간: {elapsed:.1f}초")
                
                if elapsed >= 19:
                    print(f"\n✅ 필수 4 통과: 20초 지연 정상 동작")
                    return True
                else:
                    print(f"\n❌ 필수 4 실패: 지연 미작동 ({elapsed:.1f}초)")
                    return False
                    
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False

async def test_5_parsing():
    """필수 5: 파싱 테스트"""
    print("\n" + "=" * 80)
    print("필수 5: 파싱 테스트 (MCP 프로토콜)")
    print("=" * 80)
    
    server_params = StdioServerParameters(
        command="python",
        args=["main.py", "--boss_alertness", "100", "--boss_alertness_cooldown", "300"]
    )
    
    try:
        async with stdio_client(server_params) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                result = await session.call_tool("take_a_break", {})
                text = result.content[0].text
                
                is_valid, msg = validate_response(text)
                
                if is_valid:
                    print(f"✅ 응답 형식 검증 성공")
                    print(f"\n✅ 필수 5 통과")
                    return True
                else:
                    print(f"❌ 응답 형식 검증 실패: {msg}")
                    print(f"\n❌ 필수 5 실패")
                    return False
                    
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False

async def test_6_cooldown():
    """필수 6: Cooldown 테스트"""
    print("\n" + "=" * 80)
    print("필수 6: Cooldown 테스트 (MCP 프로토콜)")
    print("=" * 80)
    
    server_params = StdioServerParameters(
        command="python",
        args=["main.py", "--boss_alertness", "100", "--boss_alertness_cooldown", "10"]
    )
    
    try:
        async with stdio_client(server_params) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                # Boss Alert 올리기
                result = await session.call_tool("take_a_break", {})
                text = result.content[0].text
                boss_match = re.search(r"Boss Alert Level:\s*([0-5])", text)
                max_boss = int(boss_match.group(1))
                print(f"호출 후 Boss Alert: {max_boss}")
                
                # 15초 대기
                print(f"⏳ 15초 대기...")
                await asyncio.sleep(15)
                
                # 상태 확인 (도구 호출로 동기화)
                result = await session.call_tool("take_a_break", {})
                text = result.content[0].text
                boss_match = re.search(r"Boss Alert Level:\s*([0-5])", text)
                final_boss = int(boss_match.group(1))
                print(f"15초 후 Boss Alert: {final_boss}")
                
                if final_boss < max_boss:
                    print(f"\n✅ 필수 6 통과: 자동 감소 동작")
                    return True
                else:
                    print(f"\n❌ 필수 6 실패: 감소 미작동")
                    return False
                    
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False

async def test_all_tools():
    """모든 도구 검증"""
    print("\n" + "=" * 80)
    print("추가: 모든 도구 호출 검증 (MCP 프로토콜)")
    print("=" * 80)
    
    server_params = StdioServerParameters(
        command="python",
        args=["main.py"]
    )
    
    try:
        async with stdio_client(server_params) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                # 도구 목록 조회
                tools_response = await session.list_tools()
                print(f"\n📋 등록된 도구: {len(tools_response.tools)}개")
                
                for tool in tools_response.tools:
                    print(f"  • {tool.name}: {tool.description}")
                
                # 모든 도구 호출
                print(f"\n🧪 모든 도구 호출 테스트:")
                for tool in tools_response.tools:
                    try:
                        result = await session.call_tool(tool.name, {})
                        text = result.content[0].text
                        
                        is_valid, msg = validate_response(text)
                        if is_valid:
                            print(f"  ✅ {tool.name}")
                        else:
                            print(f"  ❌ {tool.name}: {msg}")
                    except Exception as e:
                        print(f"  ❌ {tool.name}: {e}")
                
                return True
                    
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False

async def main():
    print("\n")
    print("=" * 80)
    print("🎯 MCP Client를 이용한 실제 검증 (심사원 방식)")
    print("=" * 80)
    print()
    
    results = {}
    
    print("█" * 80)
    print("필수 시나리오 검증 (MCP 프로토콜 사용)")
    print("█" * 80)
    
    results['1'] = await test_1_command_line_parameters()
    results['2'] = await test_2_continuous_rest()
    results['3'] = await test_3_stress_accumulation()
    results['4'] = await test_4_delay()
    results['5'] = await test_5_parsing()
    results['6'] = await test_6_cooldown()
    
    print("\n" + "█" * 80)
    print("추가 검증")
    print("█" * 80)
    await test_all_tools()
    
    # 최종 결과
    print("\n" + "=" * 80)
    print("📊 최종 평가 결과 (MCP Client 방식)")
    print("=" * 80)
    
    required = [results.get('1'), results.get('2'), results.get('3'),
                results.get('4'), results.get('5'), results.get('6')]
    
    print("\n필수 시나리오:")
    for i, result in enumerate(required, 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  필수 {i}: {status}")
    
    if all(required):
        print("\n" + "✅" * 40)
        print("✅ 모든 필수 시나리오 통과! (MCP 프로토콜)")
        print("✅ 심사원 검증 방식으로도 통과 가능!")
        print("✅" * 40)
    else:
        print("\n" + "❌" * 40)
        print("❌ 일부 시나리오 미통과")
        print("❌" * 40)

if __name__ == "__main__":
    asyncio.run(main())