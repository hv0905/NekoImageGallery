from app.Services.vector_db_context import VectorDbContext


async def main():
    context = VectorDbContext()
    await context.initialize_collection()
