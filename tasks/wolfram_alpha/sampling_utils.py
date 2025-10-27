import ell
import random
from typing import Literal
from pydantic import BaseModel, Field

from tasks.instruction_utils import get_instruction


def get_wolfram_search_query_generator():
    class WolframQuery(BaseModel):
        query: str = Field(description="Search query for Wolfram Alpha")

    @ell.complex(model="gpt-4o", response_format=WolframQuery)
    def lmp(persona: str):
        return [
            ell.system(f"You are {persona}"),
            ell.user(
                "Generate a query you would search on Wolfram Alpha to get a factual or mathematical answer. "
                "This query should relate to your profession or interests. "
                "Examples: 'integrate x^2', 'population of Brazil in 2023', 'boiling point of water', 'mass of an electron'."
            ),
        ]

    def get_query(persona: str) -> str:
        return lmp(persona).parsed.query  # type: ignore

    return get_query


def get_wolfram_equation_generator():
    class WolframQuery(BaseModel):
        query: str = Field(description="Mathematical equation question for Wolfram Alpha")

    @ell.complex(model="gpt-4o", response_format=WolframQuery)
    def lmp(persona: str):
        return [
            ell.system(f"You are {persona}"),
            ell.user(
                "Generate a mathematical query you would search on Wolfram Alpha to get a step by step answer. "
                "Examples: 'integrate x^3 dx step by step', 'solve x^2 - 4 = 0 step by step', 'differentiate x^2 + 3x step by step'."
            ),
        ]

    def get_query(persona: str) -> str:
        return lmp(persona).parsed.query  # type: ignore

    return get_query


def get_wolfram_plot_generator():
    class WolframQuery(BaseModel):
        query: str = Field(description="Plot expression question for Wolfram Alpha")

    @ell.complex(model="gpt-4o", response_format=WolframQuery)
    def lmp(persona: str):
        return [
            ell.system(f"You are {persona}"),
            ell.user(
                "Generate a query you would search on Wolfram Alpha to get an expression plotted. "
                "Examples: 'plot sin(x)', 'plot x^2 + 3x - 5', 'plot tan(x) from -pi to pi', 'plot x^3 - 6x'."
            ),
        ]

    def get_query(persona: str) -> str:
        return lmp(persona).parsed.query  # type: ignore

    return get_query


def get_wolfram_comparison_generator():
    class WolframQuery(BaseModel):
        itemA: str = Field(description="Item A that will be compared to Item B")
        itemB: str = Field(description="Item B that will be compared to Item A")

    @ell.complex(model="gpt-4o", response_format=WolframQuery)
    def lmp(persona: str):
        return [
            ell.system(f"You are {persona}"),
            ell.user(
                "Generate a two quantities you would compare on Wolfram Alpha. "
                "Examples: '(population of Texas, population of California)', '(GDP of Germany, GDP of France)', '(area of the Moon, area of Mars)'."
            ),
        ]

    def get_query(persona: str) -> str:
        out = lmp(persona).parsed
        return out.itemA, out.itemB  # type: ignore

    return get_query


def create_wolfram_search_task(query: str):
    return [dict(
        task_type="wolfram_search",
        query=query,
        steps=[
            "If you are not already on the Wolfram Alpha website, go to url https://www.wolframalpha.com",
            f"Type '{query}' into the search bar and press Enter.",
            "Wait for the answer to load.",
            "View and interpret the main result shown.",
        ],
    )]


def create_wolfram_step_by_step_task(query):
    return [dict(
        task_type="wolfram_step_by_step_solution",
        query=query,
        steps=[
            "Go to https://www.wolframalpha.com",
            f"Type '{query}' into the search bar and press Enter.",
            "Click 'Step-by-step solution' if available.",
            "Read through the steps shown to understand the method. If you need a Pro account to see the answer, let the user know.",
        ],
    )]


def create_wolfram_plot_expression_task(expression):
    return [dict(
        task_type="wolfram_plot_expression",
        expression=expression,
        steps=[
            "Go to https://www.wolframalpha.com",
            f"Type '{expression}' into the search bar.",
            "Press Enter.",
            "Wait for the plot to load.",
            "Verify that the graph looks correct.",
        ],
    )]


def create_wolfram_compare_quantities_task(a, b):
    return [dict(
        task_type="wolfram_compare_quantities",
        quantity_a=a,
        quantity_b=b,
        steps=[
            "Go to https://www.wolframalpha.com",
            f"Type '{a} vs {b}' into the search bar and press Enter.",
            "Wait for the results to load.",
            "Compare the two values and summarize which is greater or more significant.",
        ],
    )]


def create_wolfram_category_navigation_task():
    CATEGORIES = [
        "Step-by-Step Solutions", "Elementary Math", "Algebra", "Plotting & Graphics", "Calculus & Analysis",
        "Geometry", "Differential Equations", "Statistics",
        "Units & Measures", "Physics", "Chemistry", "Engineering", "Computational Sciences",
        "Earth Sciences", "Materials", "Transportation",
        "People", "Arts & Media", "Dates & Times", "Words & Linguistics", "Money & Finance",
        "Food & Nutrition", "Political Geography", "History",
        "Personal Health", "Personal Finance", "Surprises", "Entertainment", "Household Science",
        "Household Math", "Hobbies", "Today's World"
    ]
    
    category = random.choice(CATEGORIES)

    return [dict(
        task_type="wolfram_choose_category",
        category=category,
        steps=[
            "Go to https://www.wolframalpha.com",
            "Scroll down to the section showing broad categories (e.g. Mathematics, Science & Tech, etc.)",
            f"Find and click on the category titled '{category}'",
            "Wait for the new page to load.",
        ],
    )]


def create_wolfram_problem_generator_task():
    PROBLEM_GENERATOR_TOPICS = {
        "Arithmetic": [
            "Add", "Subtract", "Multiply", "Divide",
            "Add and subtract", "Multiply and divide",
            "Order of Operations"
        ],
        "Fractions": [
            "Add with common denominators", "Subtract with common denominators",
            "Add with uncommon denominators", "Subtract with uncommon denominators",
            "Multiply", "Divide", "Simplify",
            "Add and subtract", "Multiply and divide"
        ],
        "Number Theory": [
            "Divisibility test", "Primality test", "Prime factorization",
            "Divisors", "Greatest common divisor", "Least common multiple",
            "GCD and LCM", "Relatively prime test"
        ],
        "Algebra": [
            "Add radicals", "Subtract radicals", "Multiply radicals", "Distribute radicals",
            "Rationalize", "Simplify radicals",
            "Add complex numbers", "Subtract complex numbers", "Multiply complex numbers",
            "Divide complex numbers", "Find the norm",
            "Evaluate polynomial", "Add polynomials", "Subtract polynomials",
            "Expand", "Factor", "Binomial expansion",
            "Solve one-step equations", "Solve two-step equations", "Solve multi-step equations",
            "Solve quadratic equations"
        ],
        "Calculus": [
            "Basic integrals", "Integration by parts", "U-substitution",
            "Derivatives (power rule)", "Product rule", "Quotient rule",
            "Chain rule"
        ],
        "Linear Algebra": [
            "Add vectors", "Dot product", "Cross product",
            "Add matrices", "Determinant", "Inverse",
            "Eigenvalues", "Row reduction"
        ],
        "Statistics": [
            "Mean", "Median", "Mode", "Range", "Variance",
            "Standard deviation", "Quartiles"
        ]
    }

    category = random.choice(list(PROBLEM_GENERATOR_TOPICS.keys()))
    topic = random.choice(PROBLEM_GENERATOR_TOPICS[category])

    return [dict(
        task_type="wolfram_problem_generator",
        category=category,
        topic=topic,
        steps=[
            "Go to https://www.wolframalpha.com",
            "Click on 'Apps' in the top navigation bar.",
            "Then click on 'Problem Generator'.",
            f"Click into the category '{category}'.",
            f"Then choose the problem type '{topic}'.",
            "Wait for the problem to load.",
            "Tell the user how you would try to solve the problem.",
        ],
    )]


def generate_wolfram_task(
    persona: str,
    task_type: Literal[
        "wolfram_search", 
        "wolfram_choose_category", 
        "wolfram_step_by_step_solution", 
        "wolfram_plot_expression", 
        "wolfram_compare_quantities",
        "wolfram_problem_generator",
    ]
):
    tasks = []

    if task_type == "wolfram_search":
        get_query = get_wolfram_search_query_generator()
        query = get_query(persona)
        tasks.extend(create_wolfram_search_task(query))

    elif task_type == "wolfram_step_by_step_solution":
        get_query = get_wolfram_equation_generator()
        query = get_query(persona)
        tasks.extend(create_wolfram_step_by_step_task(query))

    elif task_type == "wolfram_plot_expression":
        get_query = get_wolfram_plot_generator()
        query = get_query(persona)
        tasks.extend(create_wolfram_plot_expression_task(query))

    elif task_type == "wolfram_compare_quantities":
        get_query = get_wolfram_comparison_generator()
        itemA, itemB = get_query(persona)
        tasks.extend(create_wolfram_compare_quantities_task(itemA, itemB))

    elif task_type == "wolfram_choose_category":
        tasks.extend(create_wolfram_category_navigation_task())

    elif task_type == "wolfram_problem_generator":
        tasks.extend(create_wolfram_problem_generator_task())

    else:
        raise ValueError(f"Unsupported task type: {task_type}")

    for task in tasks:
        task["instruction"] = get_instruction("wolfram", task["steps"]).model_dump()

    return dict(tasks=tasks)


WOLFRAM_TASK_TYPES = [
    "wolfram_search", 
    "wolfram_choose_category", 
    "wolfram_step_by_step_solution", 
    "wolfram_plot_expression", 
    "wolfram_compare_quantities",
    "wolfram_problem_generator",
]
