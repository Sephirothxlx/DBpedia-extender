import extractor

if __name__ == '__main__':
	extractor.extract("http://dbpedia.org/resource/Apple","result/test_plant_result.txt",0.6)
	extractor.extract("http://dbpedia.org/resource/Aronia","result/test_plant_result.txt",0.6)
	extractor.extract("http://dbpedia.org/resource/Bulbine","result/test_plant_result.txt",0.6)
	extractor.extract("http://dbpedia.org/resource/Strawberry","result/test_plant_result.txt",0.6)
	extractor.extract("http://dbpedia.org/resource/Willow","result/test_plant_result.txt",0.6)