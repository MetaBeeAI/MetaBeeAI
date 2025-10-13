# setup.py
from setuptools import setup, find_packages

setup(
    name="metabeeai_llm",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Environment and configuration
        "python-dotenv",
        
        # LLM and AI services
        "openai",
        "litellm",
        
        # Data processing and analysis
        "pandas",
        "numpy",
        "PyPDF2",
        "pymupdf",
        
        # Web framework and API
        "fastapi",
        "uvicorn",
        "python-multipart",
        
        # Data validation and serialization
        "pydantic",
        "PyYAML",
        
        # GUI framework
        "PyQt5",
        
        # Text processing and utilities
        "unidecode",
        "termcolor",
        
        # Progress bars and async utilities
        "tqdm",
        
        # Development and Jupyter support
        "ipykernel",
        
        # Data synthesis and reporting
        "faker",
        "reportlab",
        "matplotlib",
        
        # HTTP requests
        "requests",
    ],
    author="Rachel Parkinson",
    author_email="rachel.parkinson@biology.ox.ac.uk",
    description="MetaBeeAI LLM Pipeline for PDF processing and data extraction",
    keywords="pdf, llm, nlp, data extraction",
)