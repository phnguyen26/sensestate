from abc import ABC, abstractmethod
from random import random
import time
from typing import List, Any, Optional
from dataclasses import dataclass, field
import logging
import json
import os
from qdrant_client import QdrantClient
from qdrant_client import models

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.data_crawler import data_crawler
from utils.preprocessing import preprocessing
from utils.check_existed_url import check_if_url_existed
from config.qdrant_config import load_and_create_collection, get_qdrant_client, QDRANT_COLLECTION_NAME
from openai import OpenAI
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PipelineContext:
    data: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    client  = get_qdrant_client()

class PipelineStep(ABC):
    
    @abstractmethod
    def process(self, context: PipelineContext) -> PipelineContext:
        pass
    
    @property
    def name(self) -> str:
        return self.__class__.__name__

class CrawlStep(PipelineStep):
    
    def __init__(self, base_url: str, source_url: str = None, max_items: int = 10, count: int = 0, page_no: int = 1):
        self.base_url = base_url
        self.source_url = source_url
        self.max_items = max_items
        self.count = count
        self.page_no = page_no
    def process(self, context: PipelineContext) -> PipelineContext:
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--start-maximized')
        driver = uc.Chrome(options=options, version_main=145)
        try:
            while self.count < self.max_items:
                if self.page_no > 1: self.source_url = self.base_url + '/p' + str(self.page_no)
                else: self.source_url = self.base_url
                logger.info(f"Crawling data from {self.source_url}")
                driver.get(self.source_url)
                time.sleep(random() * 2 + 2)
                body = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".re__main-content"))
                )
                driver.execute_script("arguments[0].scrollIntoView();", body)
                items = WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, ".js__card.js__card-full-web.pr-container")
                    )
                )
                
                properties = []
                for i, item in enumerate(items[:self.max_items - self.count]):
                    a_tag = item.find_element(By.CSS_SELECTOR, '.js__product-link-for-product-id')
                    url = a_tag.get_attribute('href')
                    if check_if_url_existed(context.client, url, QDRANT_COLLECTION_NAME): continue
                    property_data = data_crawler(url, driver=driver)
                    properties.append(property_data)
                    self.count += 1
                    logger.info(f"Crawled item {self.count}/{self.max_items}")
                    # Random delay between items to mimic human behavior
                    time.sleep(random() * 3 + 1)
                
                context.data.extend(properties)
                self.page_no += 1
                    
        except Exception as e:
            logger.error(f"Error during crawling: {e}")
        finally:
            context.metadata['crawled_count'] = self.count
            driver.quit()
            return context
        
        


class PreprocessStep(PipelineStep):

    def process(self, context: PipelineContext) -> PipelineContext:
        if not context.data:
            logger.warning("No data to process")
            return context
        processed_data = []
        for item in context.data:
            try:
                processed_item = preprocessing(item)
                processed_data.append(processed_item)
            except Exception as e:
                logger.warning(f"Failed to preprocess item: {e}")
                continue
        
        context.data = processed_data
        context.metadata['processed_count'] = len(processed_data)
        logger.info(f"Preprocessed {len(processed_data)} items")
        
        return context


class EmbeddingStep(PipelineStep):
    
    def __init__(self, model_name: str = 'text-embedding-3-small', total_token: int = 0):
        self.model_name = model_name
        self.model = None
        self.total_tokens = total_token
    
    def load_model(self):
        if self.model is None:
            self.model = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def process(self, context: PipelineContext) -> PipelineContext:
        self.load_model()
        
        if not context.data:
            logger.warning("No data to embedding")
            return context
        try:
            for i in range(0,len(context.data), 5):
                start_idx, end_idx = i, i+5
                texts = [item.synthesis() for item in context.data[start_idx:end_idx]]
                response = self.model.embeddings.create(
                    input=texts,
                    model=self.model_name
                )
                self.total_tokens += response.usage.total_tokens
                for i in range(start_idx, end_idx):
                    if i == len(context.data): break
                    context.data[i].embedding = response.data[i - start_idx].embedding
        except Exception as e:
            logger.warning(f'Failed to embedding: {e}')
            return context
        finally:
            context.metadata['total_tokens'] = self.total_tokens
            logger.info("Embedding successfuly")
            return context


class DatabaseLoadStep(PipelineStep):
    
    def __init__(self):
        pass
    def process(self, context: PipelineContext) -> PipelineContext:
        
        if not context.data:
            logger.warning("No data to load")
            return context
        
        load_and_create_collection(QDRANT_COLLECTION_NAME)
        try:
            old_collection_size = context.client.get_collection(collection_name=QDRANT_COLLECTION_NAME).points_count
            ids = [i for i in range(old_collection_size, old_collection_size + len(context.data))]
            vectors = [data.embedding for data in context.data]
            payloads = [{k:v for k, v in data.__dict__.items() if k != 'embedding'} for data in context.data]
            context.client.upsert(
                collection_name = QDRANT_COLLECTION_NAME,
                points = models.Batch(
                    ids=ids,
                    vectors = vectors,
                    payloads = payloads
                )
            )
            logger.info('Load successfully')
        except Exception as e:
            logger.warning(f'Failed to load: {e}')
        finally:
            context.metadata['collection_size'] = context.client.get_collection(collection_name=QDRANT_COLLECTION_NAME).points_count
            return context


class Pipeline:

    def __init__(self, steps: List[PipelineStep] = None):
        self.steps = steps if steps is not None else []
    def add_step(self, step: PipelineStep) -> 'Pipeline':
        self.steps.append(step)
        return self
    
    def run(self) -> PipelineContext:
        context = PipelineContext()

        for step in self.steps:
            logger.info(f"Running step: {step.name}")
            try:
                context = step.process(context)
            except Exception as e:
                logger.error(f"Error in step {step.name}: {e}")
                raise
        
        logger.info("Pipeline completed successfully")
        return context