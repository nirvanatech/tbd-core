import argparse
import asyncio

import httpx
import pymongo
from bson import ObjectId

import config


async def delete_db_connection_resources(args: dict):
    data_store = pymongo.MongoClient(config.db_settings.mongodb_uri)[
        config.db_settings.mongodb_db_name
    ]
    if args["database_connection"]:
        data_store["database_connections"].delete_one(
            {"_id": ObjectId(args["db_connection_id"])}
        )

    if args["table_description"]:
        data_store["table_descriptions"].delete_many(
            {"db_connection_id": args["db_connection_id"]}
        )

    if args["instructions"]:
        data_store["instructions"].delete_many(
            {"db_connection_id": args["db_connection_id"]}
        )

    if args["finetunings"]:
        data_store["finetunings"].delete_many(
            {"db_connection_id": args["db_connection_id"]}
        )

    if args["golden_sqls"]:
        golden_sqls = data_store["golden_sqls"].find(
            {"db_connection_id": args["db_connection_id"]}
        )
        for golden_sql in golden_sqls:
            async with httpx.AsyncClient() as client:
                golden_id = str(golden_sql["_id"])
                response = await client.delete(
                    config.settings.engine_url + f"/golden-sqls/{golden_id}",
                    timeout=config.settings.default_engine_timeout,
                )
                response.raise_for_status()

    if args["generations"]:
        prompts = data_store["promtps"].find(
            {"db_connection_id": args["db_connection_id"]}
        )
        sql_generations = data_store["sql_generations"].find(
            {"prompt_id": {"$in": [str(prompt["_id"]) for prompt in prompts]}}
        )
        data_store["nl_generations"].delete_many(
            {
                "prompt_id": {
                    "$in": [
                        str(sql_generation["_id"]) for sql_generation in sql_generations
                    ]
                }
            }
        )

        data_store["sql_generations"].delete_many(
            {"prompt_id": {"$in": [str(prompt["_id"]) for prompt in prompts]}}
        )

        data_store["prompts"].delete_many(
            {"db_connection_id": args["db_connection_id"]}
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Delete database connection and optionally its related resources",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "db_connection_id",
        help="Database connection id",
    )

    parser.add_argument(
        "-d",
        "--database-connection",
        action="store_true",
        help="Delete database connection",
    )

    parser.add_argument(
        "-td",
        "--table-description",
        action="store_true",
        help="Delete table descriptions",
    )

    parser.add_argument(
        "-i",
        "--instructions",
        action="store_true",
        help="Delete instructions",
    )

    parser.add_argument(
        "-f",
        "--finetunings",
        action="store_true",
        help="Delete finetunings",
    )

    parser.add_argument(
        "-gs",
        "--golden-sqls",
        action="store_true",
        help="Delete golden sqls",
    )

    parser.add_argument(
        "-g",
        "--generations",
        action="store_true",
        help="Delete generations",
    )

    args = vars(parser.parse_args())

    asyncio.run(delete_db_connection_resources(args))
