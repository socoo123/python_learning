"""
Ch34 作业测试。运行: uv run pytest 06_leetcode/ch34/test_ch34_assignment.py -v

每题一个 TestXxx 类,覆盖:正常用例 >= 2 + 边界(空 / 单元素 / 重复 / k 极值)。
断言值全部手工验算,与 tutorial 示例一一对应(对齐 LC347/703/215/346/35/1480/189/509)。
"""
from ch34_assignment import (
    array_report,
    char_frequency,
    fib,
    kth_largest,
    moving_averages,
    rotate_array,
    running_sum,
    search_insert_pos,
    sort_students,
    sum_by_category,
)


# ---------- §34.2 char_frequency ----------
class TestCharFrequency:
    def test_basic(self):
        # b:3 a:2 c:1,降序
        assert char_frequency("aabbbc") == [("b", 3), ("a", 2), ("c", 1)]

    def test_ties_keep_first_seen_order(self):
        # m:1 i:4 s:4 p:2;i 与 s 同 4 次,i 先出现所以排前
        assert char_frequency("mississippi") == [("i", 4), ("s", 4), ("p", 2)]

    def test_empty(self):
        assert char_frequency("") == []

    def test_fewer_than_three_returns_actual_count(self):
        assert char_frequency("ab") == [("a", 1), ("b", 1)]

    def test_single_char(self):
        assert char_frequency("aaaa") == [("a", 4)]

    def test_top_three_among_many(self):
        # a:3 b:3 c:2 d:1,只取前 3;a 比 b 先出现
        result = char_frequency("aaabbbccd")
        assert result == [("a", 3), ("b", 3), ("c", 2)]

    def test_returns_tuples_of_char_and_count(self):
        result = char_frequency("aabbbc")
        assert all(isinstance(t, tuple) and len(t) == 2 for t in result)
        assert all(isinstance(c, str) and isinstance(n, int) for c, n in result)


# ---------- §34.3 sum_by_category ----------
class TestSumByCategory:
    def test_basic_aggregation(self):
        records = [("书", 30), ("衣", 200), ("书", 25)]
        assert sum_by_category(records) == {"书": 55, "衣": 200}

    def test_negative_amounts(self):
        # 退款:负数直接累加
        assert sum_by_category([("书", 30), ("书", -5)]) == {"书": 25}

    def test_empty(self):
        assert sum_by_category([]) == {}

    def test_single_record(self):
        assert sum_by_category([("食", 12)]) == {"食": 12}

    def test_many_categories(self):
        records = [("a", 1), ("b", 2), ("a", 3), ("c", 4), ("b", 5)]
        assert sum_by_category(records) == {"a": 4, "b": 7, "c": 4}

    def test_returns_plain_dict(self):
        # 返回普通 dict,不是 defaultdict(避免下游误触发自动建 key)
        result = sum_by_category([("书", 30)])
        assert type(result) is dict


# ---------- §34.4 kth_largest ----------
class TestKthLargest:
    def test_k2(self):
        assert kth_largest([3, 2, 1, 5, 6, 4], 2) == 5

    def test_k1_returns_max(self):
        assert kth_largest([3, 2, 1, 5, 6, 4], 1) == 6

    def test_k_equals_len_returns_min(self):
        assert kth_largest([3, 2, 1, 5, 6, 4], 6) == 1

    def test_single_element(self):
        assert kth_largest([1], 1) == 1

    def test_duplicates(self):
        # 降序 6,5,5,4,... 第 4 大 = 4
        assert kth_largest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4) == 4

    def test_negative_numbers(self):
        # [-1, -5, -3] 降序 -1,-3,-5,第 2 大 = -3
        assert kth_largest([-1, -5, -3], 2) == -3

    def test_two_elements(self):
        assert kth_largest([2, 1], 1) == 2
        assert kth_largest([2, 1], 2) == 1


# ---------- §34.5 moving_averages ----------
class TestMovingAverages:
    def test_size2(self):
        # [1]=1.0 [1,2]=1.5 [2,3]=2.5 [3,8]=5.5
        assert moving_averages([1, 2, 3, 8], 2) == [1.0, 1.5, 2.5, 5.5]

    def test_size3(self):
        # [3]=3.0 [3,6]=4.5 [3,6,9]=6.0 [6,9,12]=9.0
        assert moving_averages([3, 6, 9, 12], 3) == [3.0, 4.5, 6.0, 9.0]

    def test_empty(self):
        assert moving_averages([], 3) == []

    def test_size1_returns_elements_as_float(self):
        assert moving_averages([1, 2, 3], 1) == [1.0, 2.0, 3.0]

    def test_size_larger_than_len(self):
        # 窗口永远装不满,按实际长度平均
        assert moving_averages([1, 2], 5) == [1.0, 1.5]

    def test_window_evicts_oldest(self):
        # 关键行为:第 4 步时 1 已被踢出,窗口是 [10, 3] 不是 [1, 10, 3] 的子集平均
        # [1]=1.0 [1,10]=5.5 [1,10,3]=14/3 [10,3,5]=6.0 —— 用能验证踢旧的精确值:
        # size=2:[1]=1.0 [1,10]=5.5 [10,3]=6.5 [3,5]=4.0
        assert moving_averages([1, 10, 3, 5], 2) == [1.0, 5.5, 6.5, 4.0]


# ---------- §34.6 search_insert_pos ----------
class TestSearchInsertPos:
    def test_target_found(self):
        assert search_insert_pos([1, 3, 5, 6], 5) == 2

    def test_insert_in_middle(self):
        assert search_insert_pos([1, 3, 5, 6], 2) == 1

    def test_insert_at_end(self):
        assert search_insert_pos([1, 3, 5, 6], 7) == 4

    def test_insert_at_start(self):
        assert search_insert_pos([1, 3, 5, 6], 0) == 0

    def test_empty_array(self):
        assert search_insert_pos([], 5) == 0

    def test_single_element_found(self):
        assert search_insert_pos([1], 1) == 0

    def test_single_element_insert_before(self):
        assert search_insert_pos([2], 1) == 0

    def test_single_element_insert_after(self):
        assert search_insert_pos([2], 3) == 1

    def test_duplicates_returns_leftmost(self):
        # 有重复时 bisect_left 返回最左 >= target 的位置
        assert search_insert_pos([1, 2, 2, 2, 3], 2) == 1


# ---------- §34.7 sort_students ----------
class TestSortStudents:
    def test_score_desc_name_asc(self):
        records = [("amy", 90), ("bob", 95), ("ada", 95), ("zed", 80)]
        assert sort_students(records) == [
            ("ada", 95), ("bob", 95), ("amy", 90), ("zed", 80),
        ]

    def test_all_same_score_sorted_by_name(self):
        records = [("c", 60), ("a", 60), ("b", 60)]
        assert sort_students(records) == [("a", 60), ("b", 60), ("c", 60)]

    def test_empty(self):
        assert sort_students([]) == []

    def test_single(self):
        assert sort_students([("solo", 60)]) == [("solo", 60)]

    def test_does_not_mutate_input(self):
        # sorted 返回新列表;若误用 list.sort() 原地排,入参会被改
        records = [("amy", 90), ("ada", 95)]
        sort_students(records)
        assert records == [("amy", 90), ("ada", 95)]

    def test_distinct_scores_desc(self):
        records = [("a", 1), ("b", 3), ("c", 2)]
        assert sort_students(records) == [("b", 3), ("c", 2), ("a", 1)]


# ---------- §34.8 running_sum ----------
class TestRunningSum:
    def test_basic(self):
        assert running_sum([1, 2, 3, 4]) == [1, 3, 6, 10]

    def test_all_ones(self):
        assert running_sum([1, 1, 1, 1, 1]) == [1, 2, 3, 4, 5]

    def test_empty(self):
        assert running_sum([]) == []

    def test_single(self):
        assert running_sum([5]) == [5]

    def test_negatives(self):
        assert running_sum([-1, 1]) == [-1, 0]

    def test_mixed(self):
        # 3, 3+1=4, 4+(-2)=2, 2+5=7
        assert running_sum([3, 1, -2, 5]) == [3, 4, 2, 7]


# ---------- §34.9 rotate_array ----------
class TestRotateArray:
    def test_lc189_example(self):
        assert rotate_array([1, 2, 3, 4, 5, 6, 7], 3) == [5, 6, 7, 1, 2, 3, 4]

    def test_k_larger_than_len(self):
        # 3 % 2 = 1,右移 1 位
        assert rotate_array([1, 2], 3) == [2, 1]

    def test_k_zero(self):
        assert rotate_array([1, 2, 3], 0) == [1, 2, 3]

    def test_empty(self):
        # 不判空会 ZeroDivisionError(k % 0)
        assert rotate_array([], 5) == []

    def test_k_equals_len(self):
        # 整圈,内容不变
        assert rotate_array([1, 2, 3], 3) == [1, 2, 3]

    def test_single_element(self):
        assert rotate_array([9], 100) == [9]

    def test_returns_new_list(self):
        # 返回新列表,不改入参
        nums = [1, 2, 3]
        result = rotate_array(nums, 1)
        assert result == [3, 1, 2]
        assert nums == [1, 2, 3]
        assert result is not nums


# ---------- §34.10 fib ----------
class TestFib:
    def test_base_cases(self):
        assert fib(0) == 0
        assert fib(1) == 1

    def test_small_values(self):
        assert fib(2) == 1
        assert fib(3) == 2
        assert fib(4) == 3
        assert fib(5) == 5

    def test_fib_10(self):
        assert fib(10) == 55

    def test_fib_20(self):
        assert fib(20) == 6765

    def test_recurrence(self):
        for n in range(2, 30):
            assert fib(n) == fib(n - 1) + fib(n - 2)

    def test_fib_50_fast_with_memoization(self):
        # 裸递归这里会指数爆炸;lru_cache 后 O(n) 秒出
        assert fib(50) == 12586269025


# ---------- §34.11 array_report ----------
class TestArrayReport:
    def test_basic(self):
        # min: inf→3→1;kth: 降序 5,4,3,1,1 第 2 大 = 4;前缀和 3,4,8,9,14
        assert array_report([3, 1, 4, 1, 5], 2) == {
            "count": 5,
            "min": 1,
            "kth_largest": 4,
            "prefix_sums": [3, 4, 8, 9, 14],
        }

    def test_single_element(self):
        assert array_report([7], 1) == {
            "count": 1,
            "min": 7,
            "kth_largest": 7,
            "prefix_sums": [7],
        }

    def test_empty(self):
        assert array_report([], 1) == {
            "count": 0,
            "min": None,
            "kth_largest": None,
            "prefix_sums": [],
        }

    def test_negative_min(self):
        # inf 哨兵必须能被负数刷新;若错用 0 初始化这里会露馅
        result = array_report([-3, -1, -2], 1)
        assert result["min"] == -3
        assert result["kth_largest"] == -1
        assert result["prefix_sums"] == [-3, -4, -6]

    def test_first_element_is_min(self):
        # 第一个元素就必须刷新哨兵;若哨兵错用成小数值会露馅
        result = array_report([1, 2, 3], 3)
        assert result["min"] == 1
        assert result["kth_largest"] == 1
