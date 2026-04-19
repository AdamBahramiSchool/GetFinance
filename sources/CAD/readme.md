https://money.tmx.com/


https://app-money.tmx.com/graphql

{
    "operationName": "getTimeSeriesData",
    "variables": {
        "symbol": "^TSX",
        "interval": 10,
        "startDateTime": 1775719140,
        "endDateTime": 1776151140
    },
    "query": "query getTimeSeriesData($symbol: String!, $freq: String, $interval: Int, $start: String, $end: String, $startDateTime: Int, $endDateTime: Int) {\n  getTimeSeriesData(\n    symbol: $symbol\n    freq: $freq\n    interval: $interval\n    start: $start\n    end: $end\n    startDateTime: $startDateTime\n    endDateTime: $endDateTime\n  ) {\n    dateTime\n    open\n    high\n    low\n    close\n    volume\n    __typename\n  }\n}"
}

https://app-money.tmx.com/graphql
{
    "operationName": "GetGamAdTargeting",
    "variables": {},
    "query": "query GetGamAdTargeting {\n  gamAdTargeting {\n    data {\n      ticker\n      key\n      value\n      __typename\n    }\n    __typename\n  }\n}"
}


https://money.tmx.com/_next/data/XtrBVqKaoNcQNedvG9LwP/en/canadian-markets.json


https://app-money.tmx.com/graphql

{
    "operationName": "getETFs",
    "variables": {
        "page": 1
    },
    "query": "query getETFs($page: Int) {\n  getETFs(page: $page) {\n    symbol\n    longname\n    unitprice\n    pricetoearnings\n    __typename\n  }\n}"
}


{
    "operationName": "getETFs",
    "variables": {
        "page": 1
    },
    "query": "query getETFs($page: Int) {\n  getETFs(page: $page) {\n    symbol\n    longname\n    unitprice\n    close\n    prevClose\n    pricetoearnings\n    pricetobook\n    beta1y\n    beta2y\n    beta3y\n    avgdailyvolume\n    dividendfrequency\n    __typename\n  }\n}"
}


{
    "operationName": "getDividendsForSymbol",
    "variables": {
        "symbol": "RY",
        "page": 3,
        "batch": 10
    },
    "query": "query getDividendsForSymbol($symbol: String!, $page: Int, $batch: Int) {\n  dividendHistory: getDividendsForSymbol(\n    symbol: $symbol\n    page: $page\n    batch: $batch\n  ) {\n    pageNumber\n    hasNextPage\n    dividends {\n      exDate\n      amount\n      currency\n      payableDate\n      declarationDate\n      recordDate\n      __typename\n    }\n    __typename\n  }\n}"
}

