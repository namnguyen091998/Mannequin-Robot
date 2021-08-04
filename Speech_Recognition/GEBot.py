#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import math
from random import randint
from Helper.DesignPattern import Singleton
from Helper.JaroWinklerDistance import JaroWinklerDistance

class GEBot:
    __metaclass__ = Singleton

    def __init__(self):
        with open("./Data/eng.json", "r") as data_file:
            self.__eng = json.load(data_file)

        with open("./Data/vni.json", "r", encoding="utf8") as data_file:
            self.__vni = json.load(data_file)

        self.__cntQuestions = 0
        self.__numQuestions = len(self.__eng) + len(self.__vni)
        self.__questions = [""] * self.__numQuestions
        self.__wordsMap = dict()
        self.__buildWordsMap(self.__eng)
        self.__buildWordsMap(self.__vni)
        self.__buildTFIDF()

    def __buildWordsMap(self, dict):
        for key in dict.keys():
            self.__questions[self.__cntQuestions] = key
            for word in key.split(' '):
                weights = self.__wordsMap.get(word, [])
                if len(weights) == 0:
                    weights = [0] * self.__numQuestions
                    self.__wordsMap[word] = weights
                weights[self.__cntQuestions] += 1
            self.__cntQuestions += 1

    def __buildTFIDF(self):
        for key in self.__wordsMap.keys():
            weights = self.__wordsMap[key]
            maxFreq = max(weights) * 1.0
            numContained = (len(weights) - weights.count(0)) * 1.0
            idf = math.log(self.__numQuestions / numContained, 2)
            idx = 0
            while idx < self.__numQuestions:
                if weights[idx] > 0:
                    tf = weights[idx] / maxFreq
                    weights[idx] = tf * idf
                idx += 1

    def __analyze(self, question):
        keys = self.__wordsMap.keys()
        jaroWinklerDistance = JaroWinklerDistance()
        scoreTable = [0] * self.__numQuestions
        words = set(question.split(' '))
        for word in words:
            filtered = [w for w in keys if jaroWinklerDistance.get_jaro_distance(word, w) > 0.9]
            if len(filtered) > 0:
                for w in filtered:
                    weights = self.__wordsMap[w]
                    distance = jaroWinklerDistance.get_jaro_distance(word, w)
                    weights = [x * distance for x in weights]
                    weights = [scoreTable, weights]
                    scoreTable = [sum(x) for x in zip(*weights)]

        maxScore = max(scoreTable)
        if maxScore == 0:
            return question, 0

        validQuestionIndices = [idx for idx in range(0, len(scoreTable)) if scoreTable[idx] == maxScore]
        for i in validQuestionIndices:
            if self.__questions[i] == question:
                return question, 10

        idx = randint(0, len(validQuestionIndices) - 1)
        return self.__questions[int(list(validQuestionIndices)[idx])], maxScore

    def ask(self, question):
        question, score = self.__analyze([question.lower()][0])
        answers = self.__eng.get(question, []) # Sorry! I don't understand what you mean!
        if len(answers) < 2: answers = self.__vni.get(question, [u"Sorry! I dont understand"])
        idx = randint(0, len(answers) - 1)
        return question, answers[idx].encode('utf_8'), score
