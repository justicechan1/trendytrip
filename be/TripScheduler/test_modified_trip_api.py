import json
import sys
import os
import time
from datetime import datetime

# 현재 파일 위치 기준 경로 잡기
THIS_DIR = os.path.dirname(os.path.abspath(__file__))           # ...\TripScheduler
TRIPREC_SYS_DIR = os.path.join(THIS_DIR, 'TripRecommendationSystem')

# Add TripRecommendationSystem to path
if TRIPREC_SYS_DIR not in sys.path:
    sys.path.insert(0, TRIPREC_SYS_DIR)

from TripRecommendationSystem.trip_planner_api import plan_trip

def main():
    # Load test data - __file__ 기준으로 안전하게
    json_file_path = os.path.join(
        THIS_DIR,
        'TripRecommendationSystem',
        'src',
        'testing',
        'test_data',
        'basic_3day_jeju.json'
    )

    print("Testing modified trip_planner with scheduler_api...")
    print(f"Loading test data from: {json_file_path}")

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)

        print("Input data:")
        print(json.dumps(input_data, indent=2, ensure_ascii=False))
        print("\n" + "="*50 + "\n")

        print("Running modified trip_api.plan_trip() (using scheduler_api)...")
        start_time = time.time()
        start_datetime = datetime.now()
        print(f"시작 시간: {start_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")

        result = plan_trip(input_data, use_mock=False)

        end_time = time.time()
        end_datetime = datetime.now()
        execution_time = end_time - start_time

        print(f"종료 시간: {end_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        print(f"총 실행 시간: {execution_time:.3f}초")
        print(f"실행 시간 (분:초): {int(execution_time//60)}:{execution_time%60:06.3f}")
        print("="*50)

        print("Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        print("\n" + "="*50)
        print("실행 결과 요약")
        print("="*50)

        if result.get('success'):
            print(f"SUCCESS: {len(result['day_results'])} days planned")
            print(f"총 실행 시간: {execution_time:.3f}초")
            print(f"일 평균 처리 시간: {execution_time/len(result['day_results']):.3f}초/일")

            print("\n일차별 방문지 수:")
            total_visits = 0
            for day_result in result['day_results']:
                visits_count = len(day_result['visits'])
                path_count = len(day_result.get('path', []))
                total_visits += visits_count
                print(f"  Day {day_result['day_number']}: {visits_count} visits, {path_count} path segments")

            print(f"\n통계:")
            print(f"  총 방문지 수: {total_visits}개")
            print(f"  방문지당 평균 처리 시간: {execution_time/total_visits:.3f}초/방문지")

            output_file = os.path.join(THIS_DIR, 'test_modified_trip_api_output.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"  결과 저장: {output_file}")
        else:
            print(f"FAILED: {result.get('error')}")
            print(f"실행 시간: {execution_time:.3f}초 (실패)")

    except FileNotFoundError:
        print(f"Error: Could not find file {json_file_path}")
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
