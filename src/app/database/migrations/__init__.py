from .dev_initial import apply as apply_dev_initial


async def apply_migrations(Session):
    async with Session.begin() as session:
        await apply_dev_initial(session)
