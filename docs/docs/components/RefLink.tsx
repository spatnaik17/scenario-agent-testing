export const RefLink = ({
  link,
  children,
}: {
  link: string;
  children: React.ReactNode;
}) => {
  return (
    <a
      href={`/reference/python/scenario/${link}`}
      target="reference"
      className="underline decoration-dotted decoration-gray-400 hover:no-underline"
    >
      {children}
    </a>
  );
};
