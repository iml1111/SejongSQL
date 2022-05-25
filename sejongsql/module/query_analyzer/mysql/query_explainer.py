"""
SQL Query Explainer
"""
from collections import namedtuple
from module.query_analyzer.mysql.query_validator import SELECTQueryValidator


Report = namedtuple(
    'Report',
    ['msg', 'query_cost', 'warnings', 'report_type'],
    defaults=(None, None, None, 'query_explainer')
)


class QueryExplainer(SELECTQueryValidator):

    def explain_query(self, query: str):
        valid_report = self.check_query(query=query, collect_explain=True)
        if not valid_report.result:
            return valid_report
        explain_table = valid_report.body['explain']['table']
        explain_json = valid_report.body['explain']['json']
        query_cost = explain_json['query_block']['cost_info']['query_cost']

        # TODO 시간 초과, Time Limit : 쿼리 시간 초과 경고

        # Fulltable scan 여부 검증


        from pprint import pprint
        pprint(explain_table)
        pprint(explain_json)
        pprint(query_cost)


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv

    load_dotenv(verbose=True)

    uri = os.getenv('SSQL_DB_URI') + 'sejongsql_11013c1a_853b_4b37_9160_a52ec81129e1'
    a = QueryExplainer(uri=uri)
    a.explain_query('SELECT * FROM buytbl')