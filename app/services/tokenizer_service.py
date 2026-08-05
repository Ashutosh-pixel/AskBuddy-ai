def recursive_split(text: str, separator_index: int, separators, chunkSize: int):
    if separator_index == len(separators) - 1:
        str = ""
        result = []
        for item in text:
            if len(str) > chunkSize:
                result.append(str)
                str = ""

            str += item

        result.append(str)
        return result

    elif separator_index >= len(separators):
        return []

    elif len(text) <= chunkSize:
        result = [text]

    chunks = []
    parts = text.split(separators[separator_index])

    for i in range(len(parts)):
        if len(parts[i]) + len(separators[separator_index]) > chunkSize:
            chunks.extend(
                recursive_split(
                    parts[i] + separators[separator_index],
                    separator_index + 1,
                    separators,
                    chunkSize,
                )
            )
        else:
            chunk = parts[i] + separators[separator_index]
            if chunk.strip():
                chunks.append(chunk)

    return chunks


def merge_chunks(result, chunkSize: int):
    current_chunk = ""
    chunks = []
    for i in range(len(result)):
        if result[i].strip() == "":
            continue

        elif len(current_chunk) + len(result[i]) <= chunkSize:
            current_chunk += result[i]

        else:
            chunks.append(current_chunk)
            current_chunk = ""
            current_chunk += result[i]

    if len(current_chunk) > 0:
        chunks.append(current_chunk)

    return chunks


def split(text: str):

    separators = ["\n\n", "\n", ". ", " ", ""]
    chunkSize = 400
    separator_index = 0
    chunks = merge_chunks(
        recursive_split(text, separator_index, separators, chunkSize), chunkSize
    )

    totalsize = 0
    for i in range(len(chunks)):
        print(f"{len(chunks[i])} {chunks[i]}")
        totalsize += len(chunks[i])

    print(totalsize)


split(text = """
    Collision is short-duration interaction between two or more bodies simultaneously, causing change in their velocities due to repelling forces exerted by their interactions. The magnitude of the velocity difference just before impact is called the closing speed. All collisions conserve the total momentum of the colliding objects. What distinguishes different types of collisions is whether they also conserve kinetic energy of the system before and after the collision.



    Collisions are of two types:

    Elastic collision If all of the total kinetic energy is conserved (i.e. no energy is released as sound, heat, etc.), the collision is said to be perfectly elastic. Such a system is an idealization and cannot occur in reality, due to the second law of thermodynamics.

    Inelastic collision. If most or all of the total kinetic energy is lost (dissipated as heat, sound, etc. or absorbed by the objects themselves), the collision is said to be inelastic; such collisions involve objects coming to a full stop. An example of this is a baseball bat hitting a baseball - the kinetic energy of the bat is transferred to the ball, greatly increasing the ball's velocity. The sound of the bat hitting the ball represents the loss of energy. A "perfectly inelastic" collision (also called a "perfectly plastic" collision) is a limiting case of inelastic collision in which the two bodies coalesce after impact. An example of such a collision is a car crash, as cars crumple inward when crashing, rather than bouncing off of each other. This is by design, for the safety of the occupants and bystanders should a crash occur - the frame of the car absorbs the energy of the crash instead.


    The degree to which a collision is elastic or inelastic is quantified by the coefficient of restitution, a value that generally ranges between zero and one. A perfectly elastic collision has a coefficient of restitution of one; a perfectly inelastic collision has a coefficient of restitution of zero. The line of impact is the line that is collinear to the common normal of the surfaces that are closest or in contact during impact. This is the line along which internal force of collision acts during impact, and Newton's coefficient of restitution is defined only along this line.


    Collisions in ideal gases approach perfectly elastic collisions, as do scattering interactions of sub-atomic particles which are deflected by the electromagnetic force. Some large-scale interactions like the slingshot type gravitational interactions between satellites and planets are almost perfectly elastic.
""")
