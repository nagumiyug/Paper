import random
import csv


class Problem:
    """ 试题类 """
    def __init__(self, p=None):
        if p:
            self.id = p.id
            self.type = p.type
            self.score = p.score
            self.difficulty = p.difficulty
            self.points = p.points[:]
        else:
            self.id = 0
            self.type = 0
            self.score = 0
            self.difficulty = 0.0
            self.points = []


class DB:
    """ 题库类 """
    def __init__(self):
        self.problem_db = []
        for i in range(1, 5001):
            model = Problem()
            model.id = i
            model.difficulty = random.randint(30, 100) / 100.0

            # 设置不同题型和分数
            if i < 1001:
                model.type = 1
                model.score = 1
            elif i < 2001:
                model.type = 2
                model.score = 2
            elif i < 3001:
                model.type = 3
                model.score = 2
            elif i < 4001:
                model.type = 4
                model.score = random.randint(1, 5)
            else:
                model.type = 5
                model.score = max(int(round(model.difficulty, 1) * 10), 3)

            # 设置知识点
            points = [random.randint(1, 100) for _ in range(random.randint(1, 5))]
            model.points = points
            self.problem_db.append(model)


class Paper:
    """ 试卷类 """
    def __init__(self):
        self.id = 0
        self.total_score = 0
        self.difficulty = 0.0
        self.points = []
        self.each_type_count = []


class Unit:
    """ 种群个体类 """
    def __init__(self):
        self.id = 0
        self.adaptation_degree = 0.0
        self.kp_coverage = 0.0
        self.problem_list = []

    @property
    def difficulty(self):
        """ 计算难度系数 """
        return sum(p.difficulty * p.score for p in self.problem_list) / self.sum_score

    @property
    def problem_count(self):
        """ 题目数量 """
        return len(self.problem_list)

    @property
    def sum_score(self):
        """ 总分 """
        return sum(p.score for p in self.problem_list)


def create_initial_population(count, paper, problem_list):
    """ 初始种群 """
    unit_list = []
    for i in range(count):
        temp_unit = Unit()
        temp_unit.id = i + 1

        # 总分限制
        while paper.total_score != temp_unit.sum_score:
            temp_unit.problem_list.clear()

            # 各题型题目数量限制
            for j in range(len(paper.each_type_count)):
                one_type_problem = [p for p in problem_list if p.type == j + 1 and is_contain(paper, p)]
                for k in range(paper.each_type_count[j]):
                    index = random.randint(0, len(one_type_problem) - k - 1)
                    temp_unit.problem_list.append(one_type_problem[index])
                    one_type_problem[index], one_type_problem[-k - 1] = one_type_problem[-k - 1], one_type_problem[index]

        unit_list.append(temp_unit)

    # 计算知识点覆盖率及适应度
    unit_list = get_kp_coverage(unit_list, paper)
    unit_list = get_adaptation_degree(unit_list, paper)
    return unit_list


def get_kp_coverage(unit_list, paper):
    """ 计算知识点覆盖率 """
    for unit in unit_list:
        kp = [point for p in unit.problem_list for point in p.points]
        common = set(kp).intersection(paper.points)
        unit.kp_coverage = len(common) / len(paper.points)
    return unit_list


def get_adaptation_degree(unit_list, paper, kp_coverage_weight=0.4, difficulty_weight=0.6):
    """ 计算种群适应度 """
    for unit in unit_list:
        unit.adaptation_degree = 1 - ((1 - unit.kp_coverage) * kp_coverage_weight) - abs(unit.difficulty - paper.difficulty) * difficulty_weight
    return unit_list


def is_contain(paper, problem):
    """ 题目知识点是否符合试卷要求 """
    return any(point in paper.points for point in problem.points)


def select(unit_list, count):
    """ 选择算子（轮盘赌选择） """
    selected_unit_list = []
    all_adaptation_degree = sum(u.adaptation_degree for u in unit_list)

    while len(selected_unit_list) != count:
        rand_degree = random.random() * all_adaptation_degree
        degree = 0.0

        for unit in unit_list:
            degree += unit.adaptation_degree
            if degree >= rand_degree and unit not in selected_unit_list:
                selected_unit_list.append(unit)
                break
    return selected_unit_list


def cross(unit_list, count, paper):
    """ 交叉算子 """
    crossed_unit_list = []
    count_id = 0
    while len(crossed_unit_list) != count:
        index_one = random.randint(0, len(unit_list) - 1)
        index_two = random.randint(0, len(unit_list) - 1)

        if index_one != index_two:
            unit_one = unit_list[index_one]
            unit_two = unit_list[index_two]

            cross_position = random.randint(0, unit_one.problem_count - 2)

            score_one = unit_one.problem_list[cross_position].score + unit_one.problem_list[cross_position + 1].score
            score_two = unit_two.problem_list[cross_position].score + unit_two.problem_list[cross_position + 1].score

            if score_one == score_two:
                unit_new_one = Unit()
                unit_new_one.problem_list = unit_one.problem_list[:]
                unit_new_two = Unit()
                unit_new_two.problem_list = unit_two.problem_list[:]

                for i in range(cross_position, cross_position + 2):
                    unit_new_one.problem_list[i] = unit_two.problem_list[i]
                    unit_new_two.problem_list[i] = unit_one.problem_list[i]
                count_id += 1
                unit_new_one.id = count_id
                count_id += 1
                unit_new_two.id = count_id
                crossed_unit_list.append(unit_new_one)
                crossed_unit_list.append(unit_new_two)

    crossed_unit_list = get_kp_coverage(crossed_unit_list, paper)
    crossed_unit_list = get_adaptation_degree(crossed_unit_list, paper)
    return crossed_unit_list


def change(unit_list, problem_list, paper):
    """ 变异算子 """
    for unit in unit_list:
        index = random.randint(0, len(unit.problem_list) - 1)
        temp = unit.problem_list[index]

        problem = Problem()
        for point in temp.points:
            if point in paper.points:
                problem.points.append(point)

        other_db = [p for p in problem_list if set(p.points).intersection(problem.points) and p.score == temp.score and p.type == temp.type and p.id != temp.id]

        if other_db:
            change_index = random.randint(0, len(other_db) - 1)
            unit.problem_list[index] = other_db[change_index]

    unit_list = get_kp_coverage(unit_list, paper)
    unit_list = get_adaptation_degree(unit_list, paper)
    return unit_list


# 显示结果和其他辅助函数
def show_result(unit_list):
    """ 显示结果 """
    for unit in unit_list:
        print(f"第{unit.id}套：")
        print("题目数量\t知识点分布\t难度系数\t适应度")
        print(f"{unit.problem_count}\t{unit.kp_coverage:.2f}\t{unit.difficulty:.2f}\t{unit.adaptation_degree:.2f}\n")

# 以上是将 C# 代码转换为 Python 代码的主要部分。请注意，Python 中的 for 循环和 if 条件语句的用法与 C# 有所不同。


def is_end(unit_list, end_condition):
    """ 判断是否达到目标 """
    return any(u.adaptation_degree >= end_condition for u in unit_list)


def write_to_csv(unit_list, file_name="result.csv"):
    with open(file_name, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # 写入标题行
        writer.writerow(['ID', 'Total Score', 'Difficulty', 'Knowledge Points', 'Problem IDs'])
        for unit in unit_list:
            # 获取每个试卷的题目ID
            # problem_ids = [str(problem.id) for problem in unit.problem_list]
            problem_ids = sorted([str(problem.id) for problem in unit.problem_list])
            problem_ids_str = ' '.join(problem_ids)
            # 获取并排序每个试卷的知识点
            knowledge_points = sorted(set(point for problem in unit.problem_list for point in problem.points))
            knowledge_points_str = ' '.join(map(str, knowledge_points))
            # 写入每个试卷的详细信息
            # writer.writerow([unit.id, unit.sum_score, unit.difficulty, ' '.join(problem_ids)])
            # 写入每个试卷的详细信息
            writer.writerow([unit.id, unit.sum_score, unit.difficulty, knowledge_points_str, problem_ids_str])


def filter_units(unit_list, min_adaptation):
    """ 筛选适应度和难度符合条件的试卷 """
    return [unit for unit in unit_list if unit.adaptation_degree >= min_adaptation]


def run_genetic_algorithm():
    """ 遗传算法运行和测试函数 """
    # 初始化题库
    db = DB()

    # 设置期望试卷
    paper = Paper()
    paper.id = 1
    paper.total_score = 100
    paper.difficulty = 0.72
    paper.points = list(range(1, 82, 2))
    paper.each_type_count = [20, 5, 10, 7, 5]

    # 迭代次数计数器和适应度期望值
    count = 1
    expand = 0.98

    # 最大迭代次数
    max_iterations = 1000

    # 初始化种群
    unit_list = create_initial_population(20, paper, db.problem_db)
    print("初始种群：")
    for unit in unit_list:
        show_result([unit])
    write_to_csv(unit_list, "initial.csv")
    print("-----------------------迭代开始------------------------")

    # 开始迭代
    while not is_end(unit_list, expand):
        print(f"在第 {count} 代未得到结果")
        if count > max_iterations:
            print(f"计算 {max_iterations} 代仍没有结果，请重新设计条件！")
            break

        # 选择
        unit_list = select(unit_list, 10)

        # 交叉
        unit_list = cross(unit_list, 20, paper)

        # 变异
        unit_list = change(unit_list, db.problem_db, paper)

        count += 1

    # 显示结果
    if count <= max_iterations:
        print(f"在第 {count} 代得到结果，结果为：")
        print(f"期望试卷难度：{paper.difficulty}\n")
        # 筛选符合条件的试卷
        filtered_units = filter_units(unit_list, expand)
        show_result(filtered_units)
        # 将筛选结果写入 CSV 文件
        write_to_csv(filtered_units, "final.csv")


# 运行遗传算法
run_genetic_algorithm()

