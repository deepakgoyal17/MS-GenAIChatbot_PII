import logging

logger = logging
logger.basicConfig(filename='.\chabot.log', encoding='utf-8',format='%(asctime)s - %(message)s', level=logging.INFO)
logger.info("This is input text: ""%s", "Chatbot application started")

if __name__ == '__main__':
    logging.info('Starting unload.')